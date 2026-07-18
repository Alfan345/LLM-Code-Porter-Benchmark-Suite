import io
import re
import subprocess
import sys
import traceback


def run_python(code: str, ) -> dict:
    globals_dict = {"__builtins__": __builtins__}

    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer

    try:
        exec(code, globals_dict)
        return {"success": True, "stdout": buffer.getvalue(), "stderr": ""}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": f"{type(e).__name__}: {e}\n{traceback.format_exc()}"}
    finally:
        sys.stdout = old_stdout

def write_output(code: str, language_profile: dict) -> None:
    extension = language_profile["file_extension"]
    with open(f"main.{extension}", "w") as f:
        f.write(code)

def compile_and_run(generated_code: str, language_profile: dict) -> dict:
    write_output(code=generated_code, language_profile=language_profile)
    try:
        compile_command = language_profile["compile_command"]
        compile_process = subprocess.run(compile_command, capture_output=True, text=True)

        if compile_process.returncode != 0:
            return {
                "stage": "compile",
                "success": False,
                "output": "",
                "error": f"Compilation failed:\n{compile_process.stderr.strip()}"
            }

        # Run the compiled program and capture its output.
        run_command = language_profile["run_command"]
        run_process = subprocess.run(run_command, capture_output=True, text=True)

        if run_process.returncode != 0:
            return {
                "stage": "run",
                "success": False,
                "output": run_process.stdout.strip(),
                "error": f"Execution failed:\n{run_process.stderr.strip()}"
            }

        return {
            "stage": "success",
            "success": True,
            "output": run_process.stdout.strip(),
            "error": ""
        }

    except Exception as e:
        return {
            "stage": "error",
            "success": False,
            "output": "",
            "error": f"Unexpected error: {str(e)}"
        }

def extract_numbers(text: str) -> list[float]:
    """Extract all numbers (int or float) from a string."""
    pattern = r'-?\d+\.?\d*(?:[eE][-+]?\d+)?'
    matches = re.findall(pattern, text)
    return [float(match) for match in matches]

def compare_outputs(expected_output: str, actual_output: str, tolerance: float = None) -> dict:
    expected = expected_output.strip()
    actual = actual_output.strip()

    if expected == actual:
        return {"passed": True, "reason": ""}

    if tolerance is not None:
        expected_nums = extract_numbers(expected)
        actual_nums = extract_numbers(actual)

        if not expected_nums:
            return {
                "passed": False,
                "reason": "Expected output doesn't contain any numbers, but tolerance was provided."
            }

        if len(expected_nums) != len(actual_nums):
            return {
                "passed": False,
                "reason": f"Number count mismatch. Expected {len(expected_nums)} number(s), "
                          f"but got {len(actual_nums)} number(s).\n"
                          f"Expected numbers: {expected_nums}\n"
                          f"Actual numbers: {actual_nums}"
            }

        differences = []
        for i, (exp, act) in enumerate(zip(expected_nums, actual_nums)):
            diff = abs(exp - act)
            if diff > tolerance:
                differences.append(f"Position {i}: |{exp} - {act}| = {diff} > tolerance {tolerance}")

        if not differences:
            return {
                "passed": True,
                "reason": f"Numeric values match within tolerance ({tolerance})"
            }
        else:
            return {
                "passed": False,
                "reason": "Numeric tolerance check failed:\n" + "\n".join(differences)
            }
        
    return {
        "passed": False,
        "reason": f"Exact string mismatch.\n\n"
                  f"Expected:\n{expected}\n\n"
                  f"Actual:\n{actual}"
    }
    


def verify(python_code: str, generated_code: str, language_profile: dict, tolerance: float = 1e-6) -> dict:
    python_result = run_python(python_code)
    if not python_result["success"]:
        return {
            "passed": False,
            "stage": "python_run",
            "reason": f"Original Python code failed to run:\n{python_result['stderr']}",
            "python_output": "",
            "generated_output": ""
        }
        
    python_output = python_result["stdout"].strip()
    
    # Compile and run the generated code with the selected language profile.
    compile_run_result = compile_and_run(generated_code=generated_code, language_profile=language_profile)
    
    if not compile_run_result["success"]:
        return {
            "passed": False,
            "stage": compile_run_result["stage"],  
            "reason": compile_run_result["error"],
            "python_output": python_output,
            "generated_output": compile_run_result["output"]  
        }
    generated_output = compile_run_result["output"]

    # Compare the captured outputs.
    comparison = compare_outputs(python_output, generated_output, tolerance)

    if not comparison["passed"]:
        return {
            "passed": False,
            "stage": "mismatch", 
            "reason": f"Output mismatch! {comparison['reason']}",
            "python_output": python_output,
            "generated_output": generated_output
        }

    return {
        "passed": True,
        "stage": "success",
        "reason": "Outputs match perfectly within tolerance.",
        "python_output": python_output,
        "generated_output": generated_output
    }