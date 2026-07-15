"""
porter.py

Responsibility: orchestrate the actual "ask an LLM to port this code" workflow, including
the self-correction loop (Feature #3). This is the "agentic" core of the project.
"""
import re
from verifier import verify


def build_messages(python_code: str, language_profile: dict,
                    previous_attempt: str = None, previous_error: str = None, stage: str = None) -> list:
    """
    Build the messages list to send to the LLM, in OpenAI chat format
    (system + user, like day4.ipynb's messages_for()).

    Hint: on the FIRST attempt, previous_attempt/previous_error are None, so this looks just
    like day4.ipynb's existing messages_for(). On a RETRY, you established in Tahap 2 that
    you want to send: (a) original Python code, (b) the failed generated code, (c) the error/
    reason for failure. Think about whether that's a NEW user message appended to the same
    conversation, or a fresh conversation each time with all context repeated in one message —
    either works, but which is simpler for you to log and debug?
    """
    messages = [
        {
            "role": "system", 
            "content": language_profile["system_prompt"]
        },
        {
            "role": "user", 
            "content": f"Port this Python code to {language_profile['name']}:\n\n```python\n{python_code}\n```"
        }
    ]
    
    if previous_attempt is not None:
        if stage == "compile":
            error_prefix = f"Your previous {language_profile['name']} code failed during the COMPILATION stage. It could not be compiled."
        elif stage == "run":
            error_prefix = f"Your previous {language_profile['name']} code compiled successfully but CRASHED during the RUNTIME/EXECUTION stage."
        elif stage == "mismatch":
            error_prefix = f"Your previous {language_profile['name']} code compiled and ran successfully, but the OUTPUT WAS INCORRECT (mismatched with Python)."
        else:
            error_prefix = f"Your previous {language_profile['name']} code failed to execute properly."

        messages.append({
            "role": "assistant", 
            "content": previous_attempt
        })
        messages.append({
            "role": "user", 
            "content": (
                f"{error_prefix}\n\n"
                f"Detailed Feedback/Error:\n{previous_error}\n\n"
                f"Please analyze the problem carefully, fix the bug, and provide the fully corrected code."
            )
        })
        
    return messages


def call_model(client, model: str, messages: list) -> dict:
    """
    Call the LLM and return both the generated code AND token usage info.

    Hint: day4.ipynb's port() function already does the client.chat.completions.create() call
    and strips markdown fences from the reply. Reuse that pattern. What's different here is
    you also need response.usage (for benchmark.py's cost estimation) — don't discard it.
    Think about what shape to return, e.g. {"code": str, "usage": dict}.
    """
    api_params = {
        "model": model,
        "messages": messages
    }
    
    if any(reasoning_keyword in model.lower() for reasoning_keyword in ["o1-", "o3-"]):
        api_params["reasoning_effort"] = "medium"

    response = client.chat.completions.create(**api_params)
    reply = response.choices[0].message.content

    # Pembersihan Markdown Fence Universal menggunakan Regex
    reply = re.sub(r"^```[a-zA-Z0-9]*\s*\n", "", reply)
    reply = re.sub(r"\n\s*```$", "", reply).strip()

    usage_data = {
        "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
        "completion_tokens": getattr(response.usage, "completion_tokens", 0),
        "total_tokens": getattr(response.usage, "total_tokens", 0)
    }

    return {
        "code": reply,
        "usage": usage_data
    }


def port_with_self_correction(
    client, 
    model: str, 
    python_code: str, 
    language_profile: dict,
    max_attempts: int = 3
) -> dict:
    """
    The core agentic loop that attempts to port code and self-corrects based on compiler/output feedback.
    """
    history = []
    previous_attempt = None
    previous_error = None
    current_stage = None
    
    total_prompt_tokens = 0
    total_completion_tokens = 0
    
    for attempt in range(1, max_attempts + 1):
        # 1. Bangun message turn
        messages = build_messages(
            python_code=python_code, 
            language_profile=language_profile, 
            previous_attempt=previous_attempt, 
            previous_error=previous_error, 
            stage=current_stage
        )
        
        # 2. Panggil API LLM
        llm_result = call_model(client, model, messages)
        generated_code = llm_result["code"]
        usage = llm_result["usage"]
        
        # Akumulasi penggunaan token
        total_prompt_tokens += usage["prompt_tokens"]
        total_completion_tokens += usage["completion_tokens"]
        
        # 3. Verifikasi hasil menggunakan compiler asli
        verify_result = verify(
            python_code=python_code, 
            generated_code=generated_code, 
            language_profile=language_profile
        )
        
        # 4. Simpan record dengan membongkar seluruh isi verify_result via operator **
        record = {
            "attempt": attempt,
            "code": generated_code,
            "usage": usage,
            **verify_result  
        }
        history.append(record)
        
        # 5. Evaluasi hasil verifikasi
        if verify_result["passed"] is True:
            return {
                "success": True,
                "final_code": generated_code,
                "attempts_needed": attempt,
                "total_usage": {
                    "prompt_tokens": total_prompt_tokens,
                    "completion_tokens": total_completion_tokens,
                    "total_tokens": total_prompt_tokens + total_completion_tokens
                },
                "final_verification": verify_result, # Bersih, karena verify_result asli dari verifier
                "history": history
            }
            
        # REVISI 1: Walrus operator dibuang, kembali ke kode yang clean & readable
        if verify_result["stage"] in ["python_run", "error"]:
            break
            
        # 6. Set memori untuk iterasi loop berikutnya jika gagal dan mau di-retry
        previous_attempt = generated_code
        previous_error = verify_result["reason"]
        current_stage = verify_result["stage"]
        
    # 7. Fallback saat max_attempts habis atau terkena break kegagalan fatal
    # REVISI 2: Filter data agar hanya field asli dari verify() yang masuk ke final_verification
    if history:
        last_record = history[-1]
        final_verification_data = {
            "passed": last_record["passed"],
            "stage": last_record["stage"],
            "reason": last_record["reason"],
            "python_output": last_record["python_output"],
            "generated_output": last_record["generated_output"]
        }
    else:
        final_verification_data = {
            "passed": False, 
            "stage": "error", 
            "reason": "No attempts were executed.",
            "python_output": "",
            "generated_output": ""
        }

    return {
        "success": False,
        "final_code": history[-1]["code"] if history else "",
        "attempts_needed": len(history),
        "total_usage": {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens
        },
        "final_verification": final_verification_data,
        "history": history
    }