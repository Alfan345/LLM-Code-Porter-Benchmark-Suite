
# LLM Code Porter & Benchmark Suite

> An evaluation harness that ports Python code to high-performance C++/Rust using LLMs, automatically verifies correctness against the original program, benchmarks the results, and self-corrects when a model gets it wrong.

![status](https://img.shields.io/badge/status-active-brightgreen) ![python](https://img.shields.io/badge/python-3.13-blue) ![tests](https://img.shields.io/badge/tests-20%2B%20passing-success)

---

## The Problem

Teams experimenting with LLMs for code generation face a question that's harder than it looks: **which model should we actually trust to write performance-critical code?**

Benchmarks that only measure "did it compile" or "does it look right" miss the two things that actually matter in production:

1. **Is the output *correct*?** A model can generate code that compiles cleanly and runs fast — and still returns the wrong answer. Without automated output verification, that bug ships.
2. **Can the model recover from its own mistakes?** A single failed attempt shouldn't be the end of the story. Real engineering workflows involve iteration — compile, fail, read the error, fix, retry.

This project treats LLM code generation as a **measurable, verifiable pipeline** rather than a one-shot demo. Given a Python snippet, it asks multiple LLMs (GPT, Claude, Gemini, DeepSeek, open-source models via OpenRouter, etc.) to port it to C++ or Rust, then:

1. **Verifies** the ported code produces output identical to the original Python — not just that it compiles
2. **Benchmarks** every model on speed, cost, and reliability, side by side in one dashboard
3. **Self-corrects** automatically: if a model's code fails to compile, crashes, or produces the wrong output, the failure is fed back to the same model with a request to fix it — up to N attempts
4. **Generalises** across target languages through a pluggable language-profile system, not hardcoded C++ logic

The result is a small but real answer to "which LLM should I trust for this kind of task, and how much retrying does it actually need?"

---

## Demo

<!-- TODO: Replace this with an actual screenshot or short GIF of the Gradio UI in action.
     Suggested: record a ~15-20s screen capture of picking 2-3 models, clicking "Run Full Benchmark",
     and the results table + code view populating. A GIF reads far better on GitHub than a static image. -->

<img width="1280" height="720" alt="661c267a-e966-4e51-8c0c-7e102baf66d5" src="https://github.com/user-attachments/assets/c5465a99-48d2-4693-989a-e079e99c2750" />

*Benchmark dashboard comparing DeepSeek, Gemini, and an open-source model on the same Python→C++ porting task — all three passed verification on the first attempt.*

<!-- TODO: If you record a short video walkthrough (even a phone screen recording), link it here:
     ## Video Walkthrough
     [Watch a 2-minute walkthrough](your-video-link-here) -->

---

## Features

### 1. Automatic Correctness Verification
Executes both the original Python and the generated code against the same inputs and compares outputs programmatically — exact match for text, tolerance-based comparison for floating-point numeric output (extracted and compared within a configurable epsilon). No manual eyeballing of results.

### 2. Benchmark Dashboard
A live Gradio interface that runs the full pipeline for multiple models in one click and renders a sortable results table: model, language, pass/fail, attempts needed, compile time, execution time, speedup vs. the Python baseline, and estimated USD cost — plus a view of the last successfully generated code.

### 3. Self-Correction Loop
When generated code fails — at compile time, at runtime, or by producing a mismatched result — the failure (including the exact compiler error or output diff) is sent back to the same model as conversational context, and it gets another attempt. The loop distinguishes failures worth retrying (bugs in the generated code) from failures that aren't (a broken test case, or a missing compiler on the host) — the latter stop immediately instead of wasting API calls.

### 4. Multi-Language Target Support
Adding a new target language means adding one new entry to a language registry (compiler command, run command, file extension, system prompt) — not touching the core pipeline. Currently supports **C++** and **Rust**.

---

## Architecture

```
llm-code-porter/
├── README.md
├── requirements.txt
├── .env.example
├── app.py                  # HF Spaces entry point (thin wrapper -> src/app.py)
├── packages.txt             # Debian system deps for HF Spaces build (g++, rustc)
├── src/
│   ├── models.py            # LLM client + pricing registry
│   ├── porter.py            # LLM calls + self-correction loop (the agentic core)
│   ├── verifier.py          # Correctness verification (Python vs. generated output)
│   ├── benchmark.py         # Timing, cost estimation, dashboard data assembly
│   ├── languages/            # Per-language profiles (cpp, rust)
│   └── app.py                # Gradio UI wiring
└── tests/
    ├── test_verifier.py             # Unit tests (pure functions)
    ├── test_verifier_integration.py # Integration tests (real g++ compilation)
    └── test_porter.py               # Mocked-LLM tests for the self-correction loop
```

**Design principle:** each module answers exactly one question — `verifier.py` only decides *is this correct*, `benchmark.py` only decides *how fast/expensive*, `porter.py` only orchestrates the *LLM ↔ compiler* feedback loop. `app.py` is wiring only; it contains no business logic of its own.

---

## How It Works

```
Python code
    │
    ▼
┌─────────────────────┐
│  porter.py           │  build prompt → call LLM → get generated code
└─────────┬────────────┘
          ▼
┌─────────────────────┐
│  verifier.py          │  write file → compile → run → compare vs. Python output
└─────────┬────────────┘
          │
    passed?  ──── No ──▶ feed error back to LLM, retry (up to max_attempts)
          │
         Yes
          ▼
┌─────────────────────┐
│  benchmark.py          │  measure compile/execution time, estimate cost
└─────────┬────────────┘
          ▼
   Results table (Gradio dashboard)
```

---

## Getting Started

```bash
git clone <your-repo-url>
cd llm-code-porter
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # then fill in whichever API keys you have
```

You'll also need a C++ compiler (`g++`) and, optionally, `rustc` on your system if you want to benchmark Rust output.

Run the dashboard locally:
```bash
cd src
python app.py
```

Run the test suite:
```bash
pytest -v
```

---

## Testing

The project has three layers of automated tests:

- **Unit tests** (`test_verifier.py`) — pure-function correctness for output comparison and number extraction, no external dependencies, runs in milliseconds
- **Integration tests** (`test_verifier_integration.py`) — real end-to-end compilation with `g++`, covering success, compile-failure, and output-mismatch paths
- **Mocked agent tests** (`test_porter.py`) — the self-correction loop tested against a fake LLM client (`unittest.mock`) that deliberately returns broken code on the first call and correct code on the second, proving the retry mechanism actually works — while still compiling the generated code for real

     18 passed in 7.83s -->

---

## Sample Results

<img width="2324" height="956" alt="4b530d4f-ba25-45fb-a83b-19f3587b7d82" src="https://github.com/user-attachments/assets/77a8fce8-6b04-4f49-abed-c1b64d2084ce" />

---

## Known Limitations

- **Standard-library-only scope**: to keep the compile/run pipeline deterministic and dependency-free, generated code is instructed to use only each language's standard library — no external C++ libraries or Rust crates. A future version could support scoped dependency installation, with appropriate sandboxing.
- **Single shared working directory**: generated source files are compiled in place rather than in per-run isolated directories, so benchmark runs for a given language are currently sequential rather than parallel.
- **Deployment**: I attempted to deploy this to Hugging Face Spaces, but ran into a platform-level constraint: as of mid-2026, free-tier Gradio Spaces are being auto-assigned to ZeroGPU hardware (which requires a `@spaces.GPU`-decorated function to pass its health check), while Docker SDK — which this project needs for its `g++`/`rustc` toolchain — has moved behind a paid tier. This is a documented, widely-reported free-tier change on Hugging Face's side, not specific to this app. The app runs correctly locally (see demo above); redeploying once free-tier Docker access is restored, or on an alternative platform (e.g. Render, Fly.io), is a natural next step.

---

## Roadmap

- [x] Automatic correctness verification
- [x] Benchmark dashboard
- [x] Self-correction loop
- [x] Multi-language support (C++, Rust)
- [ ] Additional target languages (Go, JavaScript)
- [ ] Sandboxed execution (Docker, per-run isolation)
- [ ] Public deployment
- [ ] Parallel/streaming benchmark execution in the UI

---

## Why I Built This

I built this to get hands-on experience working with frontier LLMs beyond simple prompt-and-response usage — actually wiring them into a real pipeline with retries, verification, and feedback loops. It was also a deliberate exercise in prompt engineering: learning how to structure system prompts and iterative feedback messages so a model reliably produces code that compiles and behaves correctly, rather than just "looks right" on the first try.

## License

MIT
