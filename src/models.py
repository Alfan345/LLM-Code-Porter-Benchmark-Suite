"""
models.py

Responsibility: registry of LLM clients and model names, exactly like the `models`/`clients`
dicts you already built in day4.ipynb — just moved out of the notebook into a reusable module.
"""


import os
from openai import OpenAI

def load_clients() -> dict:
    """
    Membangun dan mengembalikan dictionary {nama_model: objek_client}.
    Key di sini dipetakan langsung ke nama model spesifik agar konsisten dengan pricing_table.
    Klien hanya dibuat jika API Key yang bersangkutan tersedia di env.
    """
    model_clients = {}

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openrouter_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_key,
    ) if openrouter_key else None

    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    deepseek_client = OpenAI(
        base_url="https://api.deepseek.com",
        api_key=deepseek_key,
    ) if deepseek_key else None

    gemini_key = os.getenv("GEMINI_API_KEY")
    gemini_client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=gemini_key,
    ) if gemini_key else None
    
    # Model via OpenRouter
    if openrouter_client:
        model_clients["nvidia/nemotron-3-ultra-550b-a55b:free"] = openrouter_client
       
    # Model via DeepSeek 
    if deepseek_client:
        model_clients["deepseek-chat"] = deepseek_client

    # Model via Google AI Studio
    if gemini_client:
        model_clients["gemini-2.5-flash"] = gemini_client  # Sukses terdaftar jika key Gemini ada

    return model_clients


def get_pricing_table() -> dict:
    """
    Return a dict of {model_name: {"input_per_1m": float, "output_per_1m": float}}
    Key di sini wajib SAMA PERSIS dengan key yang ada di load_clients().
    """
    return {
        "nvidia/nemotron-3-ultra-550b-a55b:free": {"input_per_1m": 0.0, "output_per_1m": 0.0},
        
        "deepseek-chat": {"input_per_1m": 0.14, "output_per_1m": 0.28},
     
        "gemini-2.5-flash": {"input_per_1m": 0.0, "output_per_1m": 0.0},
    }