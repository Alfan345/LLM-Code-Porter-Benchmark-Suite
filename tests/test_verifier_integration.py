import pytest
from languages import get_language_profile
from verifier import verify

# DATA MOCK FOR INTEGRATION TESTING
PYTHON_CODE_VALID = """
def calculate(iterations, param1, param2):
    result = 1.0
    for i in range(1, iterations+1):
        j = i * param1 - param2
        result -= (1/j)
        j = i * param1 + param2
        result += (1/j)
    return result

result = calculate(1000, 4, 1) * 4
print(f"Result: {result:.6f}")
"""

CPP_CODE_SUCCESS = """#include <iostream>
#include <iomanip>

double calculate(int iterations, double param1, double param2) {
    double result = 1.0;
    for (int i = 1; i <= iterations; ++i) {
        double j = i * param1 - param2;
        result -= (1.0 / j);
        j = i * param1 + param2;
        result += (1.0 / j);
    }
    return result;
}

int main() {
    double result = calculate(1000, 4.0, 1.0) * 4.0;
    std::cout << std::fixed << std::setprecision(6);
    std::cout << "Result: " << result << std::endl;
    return 0;
}
"""

CPP_CODE_MISMATCH = """#include <iostream>
int main() {
    std::cout << "Result: 99.999999" << std::endl;
    return 0;
}
"""

CPP_CODE_COMPILE_FAIL = """#include <iostream>
int main() {
    std::cout << "Result" << std::endl
    return 0;
}
"""


def test_verify_success_case():
    """The full pipeline should pass when both programs print the same output."""
    profile = get_language_profile("cpp")
    result = verify(PYTHON_CODE_VALID, CPP_CODE_SUCCESS, profile, tolerance=1e-5)
    
    assert result["passed"] is True
    assert result["stage"] == "success"
    assert "Result:" in result["python_output"]

def test_verify_detects_mismatch():
    """The pipeline should report a mismatch when outputs differ."""
    profile = get_language_profile("cpp")
    result = verify(PYTHON_CODE_VALID, CPP_CODE_MISMATCH, profile, tolerance=1e-5)
    
    assert result["passed"] is False
    assert result["stage"] == "mismatch"
    assert "Output mismatch!" in result["reason"]

def test_verify_detects_compile_failure():
    """The pipeline should report a compile failure when g++ rejects the code."""
    profile = get_language_profile("cpp")
    result = verify(PYTHON_CODE_VALID, CPP_CODE_COMPILE_FAIL, profile, tolerance=1e-5)
    
    assert result["passed"] is False
    assert result["stage"] == "compile"
    assert "Compilation failed" in result["reason"]