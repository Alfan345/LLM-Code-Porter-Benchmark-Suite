import sys
import time
import subprocess
import pandas as pd

def measure_python_execution_time(python_code: str, runs: int = 3) -> float:
    recorded_times = []
    
    for attempt in range(runs):
        start_time = time.perf_counter()
        try:
            subprocess.run(
                [sys.executable, "-c", python_code],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
        except Exception:  
            continue
            
        end_time = time.perf_counter()
        recorded_times.append(end_time - start_time)
        
    return min(recorded_times) if recorded_times else -1.0


def measure_compile_time(language_profile: dict) -> float:
    compile_command = language_profile.get("compile_command")
    if not compile_command:
        return 0.0
        
    start_time = time.perf_counter()
    try:
        subprocess.run(compile_command, capture_output=True, text=True, check=True)
    except Exception: 
        return -1.0
        
    end_time = time.perf_counter()
    return end_time - start_time


def measure_execution_time(language_profile: dict, runs: int = 3) -> float:
    run_command = language_profile["run_command"]
    recorded_times = []
    
    for attempt in range(runs):
        start_time = time.perf_counter()
        try:
            subprocess.run(
                run_command, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=30
            )
        except Exception: 
            continue
            
        end_time = time.perf_counter()
        recorded_times.append(end_time - start_time)
        
    return min(recorded_times) if recorded_times else -1.0


def estimate_cost(model: str, usage: dict, pricing_table: dict) -> float:
    model_pricing = pricing_table.get(model)
    if not model_pricing:
        return 0.0
        
    input_price_per_1m = model_pricing.get("input_per_1m", 0.0)
    output_price_per_1m = model_pricing.get("output_per_1m", 0.0)
    
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    
    input_cost = (prompt_tokens * input_price_per_1m) / 1_000_000
    output_cost = (completion_tokens * output_price_per_1m) / 1_000_000
    
    return input_cost + output_cost


def build_benchmark_row(
    model: str, 
    language: str, 
    verification_result: dict,
    compile_time: float, 
    execution_time: float,
    cost: float, 
    attempts_needed: int,
    python_execution_time: float
) -> dict:
    """
    Merakit satu baris utuh data metrik benchmark ke dalam format dictionary terstruktur.
    """
    passed_status = verification_result.get("passed", False)
    
    if not passed_status or execution_time <= 0 or python_execution_time <= 0:
        speedup = 0.0
    else:
        speedup = python_execution_time / execution_time

    return {
        "model": model,
        "language": language,
        "passed": passed_status,
        "attempts_needed": attempts_needed,
        "compile_time": round(compile_time, 4),
        "execution_time": round(execution_time, 4),
        "speedup_vs_python": round(speedup, 2),
        "cost": round(cost, 6)
    }


def results_to_dataframe(rows: list) -> pd.DataFrame:
    """
    Mengubah tumpukan list rows menjadi Pandas DataFrame yang siap divisualisasikan.
    """
    df = pd.DataFrame(rows)
    
    if not df.empty:
        df = df.sort_values(by=["passed", "execution_time"], ascending=[False, True]).reset_index(drop=True)
        
    return df