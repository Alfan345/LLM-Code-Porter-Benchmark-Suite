"""
languages/__init__.py

Responsibility: registry of language "profiles" so porter.py, verifier.py, and benchmark.py
never hardcode C++-specific details. Adding a new language later should mean adding one new
file here — not touching the core pipeline.

Hint: think about what fields EVERY language profile needs, at minimum:
    - name
    - file_extension (e.g. ".cpp", ".rs")
    - compile_command (list of str, like in day4.ipynb) — or None if the language is interpreted
    - run_command (list of str)
    - system_prompt (the LLM instruction — you already have this pattern in day4.ipynb)

Question to think about: for an interpreted language (say, JavaScript with Node), is
"compile_command" even meaningful? Should your profile structure support "compile_command = None"
and have the calling code skip the compile step when that's the case?
"""

LANGUAGE_REGISTRY = {
    "cpp": {
        "name": "C++",
        "file_extension": "cpp",  
        "compile_command": ["g++", "-std=c++17", "main.cpp", "-o", "main"], 
        "run_command": ["./main"],  
        "system_prompt": (
            "You are an expert C++ developer. Convert the given Python code into highly optimized C++ code.\n"
            "CRITICAL RULES:\n"
            "1. ONLY use the C++ Standard Library (e.g., <iostream>, <vector>, <cmath>).\n"
            "2. DO NOT use any external libraries or non-standard headers.\n"
            "3. Ensure the output format (stdout) matches the Python code exactly.\n"
            "4. Return ONLY the raw source code inside a standard markdown code block, no extra explanations."
        )
    },
    "rust": {
        "name": "Rust",
        "file_extension": "rs",
        "compile_command": ["rustc", "main.rs", "-o", "main"],
        "run_command": ["./main"],
        "system_prompt": (
            "You are an expert Rust developer. Convert the given Python code into highly optimized and safe Rust code.\n"
            "CRITICAL RULES:\n"
            "1. ONLY use the Rust Standard Library (modules under the `std::` namespace).\n"
            "2. DO NOT use any external dependencies, third-party libraries, or external crates (no `cargo` features available).\n"
            "3. The code must be self-contained and compilable using `rustc main.rs -o main` directly.\n"
            "4. Ensure the output format (stdout via `println!`) matches the Python code exactly.\n"
            "5. Return ONLY the raw source code inside a standard markdown code block, no extra explanations."
        )
    }
}

def get_language_profile(language: str) -> dict:
    """
    Look up a language profile by name from LANGUAGE_REGISTRY.
    """
    if not language:
        raise ValueError("Language parameter cannot be empty.")

    # Convert input to lowercase and strip whitespace for case-insensitive lookup
    key = language.lower().strip()
    
    # Normalize naming variations
    if key in ["c++", "cpp"]:
        key = "cpp"
    elif key in ["rust", "rs"]:
        key = "rust"
        
    if key not in LANGUAGE_REGISTRY:
        supported_langs = ", ".join([profile["name"] for profile in LANGUAGE_REGISTRY.values()])
        raise KeyError(
            f"Language '{language}' is not supported yet.\n"
            f"Currently supported languages are: [{supported_langs}]"
        )
        
    return LANGUAGE_REGISTRY[key]