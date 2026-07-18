import gradio as gr
import pandas as pd
from dotenv import load_dotenv

from models import load_clients, get_pricing_table
from languages import get_language_profile, LANGUAGE_REGISTRY
from porter import port_with_self_correction
from benchmark import (
    measure_python_execution_time,
    measure_compile_time,
    measure_execution_time,
    estimate_cost,
    build_benchmark_row,
    results_to_dataframe
)

load_dotenv(override=True)

def run_full_benchmark(python_code: str, selected_models: list, target_language: str):
    """
    Main callback for the benchmark button. Wire the workflow sequentially
    and delegates data row assembly and DataFrame creation to benchmark.py.
    """
    if not python_code.strip():
        return pd.DataFrame([{"error": "Python code cannot be empty."}]), "// No code generated."
    if not selected_models:
        return pd.DataFrame([{"error": "Please select at least one LLM model."}]), "// No code generated."
        
    language_profile = get_language_profile(target_language)
    available_clients = load_clients()
    pricing_table = get_pricing_table()
    
    rows = []
    last_successful_code = "// No successful code generated from selected models."
    
    # Measure the baseline execution time for the Python source.
    python_execution_time = measure_python_execution_time(python_code, runs=3)
    
    # Run the benchmark pipeline for each selected model.
    for model in selected_models:
        client_obj = available_clients.get(model)
        
        if not client_obj:
            failed_verification = {"passed": False}
            row = build_benchmark_row(
                model=model,
                language=target_language,
                verification_result=failed_verification,
                compile_time=-1.0,
                execution_time=-1.0,
                cost=0.0,
                attempts_needed=0,
                python_execution_time=python_execution_time
            )
            rows.append(row)
            continue
            
        port_result = port_with_self_correction(
            client=client_obj,
            model=model,
            python_code=python_code,
            language_profile=language_profile,
            max_attempts=3
        )
        
        final_verification = port_result["final_verification"]
        attempts_needed = port_result["attempts_needed"]
        total_usage = port_result["total_usage"]
        
        # Estimate token cost in USD.
        cost = estimate_cost(model, total_usage, pricing_table)
        
        # Measure runtime metrics only for successful translations.
        if port_result["success"] is True:
            compile_time = measure_compile_time(language_profile)
            execution_time = measure_execution_time(language_profile, runs=3)
            if "final_code" in port_result:
                last_successful_code = port_result["final_code"]
        else:
            compile_time = -1.0
            execution_time = -1.0
            
        row = build_benchmark_row(
            model=model,
            language=target_language,
            verification_result=final_verification,
            compile_time=compile_time,
            execution_time=execution_time,
            cost=cost,
            attempts_needed=attempts_needed,
            python_execution_time=python_execution_time
        )
        rows.append(row)
        
    df = results_to_dataframe(rows)
        
    return df, last_successful_code


def build_ui():
    """
    Assembles the Gradio Blocks layout for the benchmark dashboard.
    """
    available_models = list(load_clients().keys())
    available_languages = list(LANGUAGE_REGISTRY.keys())
    
    default_python_code = (
        "# Estimate Pi using the Leibniz formula\n"
        "pi_estimate = 0.0\n"
        "sign = 1\n"
        "for i in range(1, 100000, 2):\n"
        "    pi_estimate += sign * (4.0 / i)\n"
        "    sign *= -1\n"
        "print(f'Result: {pi_estimate:.4f}')"
    )

    with gr.Blocks(title="AI Transpiler Performance Benchmark Dashboard") as ui:
        gr.Markdown("# AI Transpiler and Performance Benchmark Dashboard")
        gr.Markdown(
            "Translate Python code to C++/Rust using LLMs equipped with a Self-Correction Loop, "
            "and measure execution performance metrics instantly."
        )
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Experiment Configuration")
                
                python_code_input = gr.Textbox(
                    label="Python Source Code (Baseline)",
                    lines=10,
                    value=default_python_code,
                    placeholder="Enter Python code here..."
                )
                
                target_lang_input = gr.Dropdown(
                    label="Target Language Profile",
                    choices=available_languages,
                    value=available_languages[0] if available_languages else None
                )
                
                models_input = gr.CheckboxGroup(
                    label="Select LLM Models to Benchmark",
                    choices=available_models,
                    value=[available_models[0]] if available_models else []
                )
                
                btn_run = gr.Button("Run Full Benchmark", variant="primary")
            
            with gr.Column(scale=2):
                gr.Markdown("### Metrics and Performance Analysis")
                
                results_output = gr.Dataframe(
                    label="Benchmark Results Table",
                    interactive=False
                )
                
                gr.Markdown("### Generated Code Output (Last Successful)")
                code_output = gr.Code(
                    label="Translated Code View",
                    language="cpp",
                    interactive=False
                )
                
        btn_run.click(
            fn=run_full_benchmark,
            inputs=[python_code_input, models_input, target_lang_input],
            outputs=[results_output, code_output]
        )
        
    return ui

if __name__ == "__main__":
    ui = build_ui()
    ui.launch(inbrowser=True)