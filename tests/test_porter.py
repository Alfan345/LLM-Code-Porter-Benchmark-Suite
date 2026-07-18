import pytest
from unittest.mock import MagicMock
from languages import get_language_profile
from porter import port_with_self_correction

def test_port_succeeds_on_first_attempt():
    """
    The first model response is valid and the loop stops immediately.
    """
    python_code = "print('Result:', 5 + 5)"
    cpp_profile = get_language_profile("cpp")
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = """#include <iostream>
int main() {
    std::cout << "Result: 10" << std::endl;
    return 0;
}"""
    mock_response.usage.prompt_tokens = 40
    mock_response.usage.completion_tokens = 15
    mock_response.usage.total_tokens = 55
    
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    
    result = port_with_self_correction(
        client=mock_client, 
        model="fake-free-model", 
        python_code=python_code, 
        language_profile=cpp_profile, 
        max_attempts=3
    )
    
    assert result["success"] is True
    assert result["attempts_needed"] == 1
    assert result["total_usage"]["total_tokens"] == 55
    
    assert len(result["history"]) == 1
    assert result["history"][0]["stage"] == "success"
    assert result["history"][0]["passed"] is True


def test_self_correction_succeeds_on_retry():
    """
    A compile failure on the first attempt should trigger a retry that succeeds.
    """
    python_code = "print('Result:', 5 + 5)"
    cpp_profile = get_language_profile("cpp")
    
    mock_response_fail = MagicMock()
    mock_response_fail.choices[0].message.content = """#include <iostream>
int main() {
    std::cout << "Result: 10" << std::endl // <- TYPO: Sengaja dibuat fail
    return 0;
}"""
    mock_response_fail.usage.prompt_tokens = 50
    mock_response_fail.usage.completion_tokens = 20
    mock_response_fail.usage.total_tokens = 70
    
    mock_response_success = MagicMock()
    mock_response_success.choices[0].message.content = """#include <iostream>
int main() {
    std::cout << "Result: 10" << std::endl;
    return 0;
}"""
    mock_response_success.usage.prompt_tokens = 100
    mock_response_success.usage.completion_tokens = 25
    mock_response_success.usage.total_tokens = 125
    
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [mock_response_fail, mock_response_success]
    
    result = port_with_self_correction(
        client=mock_client, 
        model="fake-free-model", 
        python_code=python_code, 
        language_profile=cpp_profile, 
        max_attempts=3
    )
    
    assert result["success"] is True
    assert result["attempts_needed"] == 2
    
    assert result["total_usage"]["total_tokens"] == 195 
    
    assert len(result["history"]) == 2
    assert result["history"][0]["stage"] == "compile"
    assert result["history"][0]["passed"] is False
    assert result["history"][1]["stage"] == "success"
    assert result["history"][1]["passed"] is True

def test_self_correction_fails_permanently():
    """
    Repeated mismatches should exhaust max_attempts and return failure.
    """
    python_code = "print('Result: 100')"
    cpp_profile = get_language_profile("cpp")
    
    responses = []
    for i in range(3):
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = """#include <iostream>
int main() {
    std::cout << "Result: 999" << std::endl; // <- Valid secara compile, tapi nilainya salah
    return 0;
}"""
        mock_resp.usage.prompt_tokens = 60
        mock_resp.usage.completion_tokens = 20
        mock_resp.usage.total_tokens = 80
        responses.append(mock_resp)
        
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = responses
    
    result = port_with_self_correction(
        client=mock_client, 
        model="fake-free-model", 
        python_code=python_code, 
        language_profile=cpp_profile, 
        max_attempts=3
    )
    
    assert result["success"] is False
    
    assert result["attempts_needed"] == 3
    assert len(result["history"]) == 3
    
    assert result["total_usage"]["total_tokens"] == 240
    
    for record in result["history"]:
        assert record["stage"] == "mismatch"
        assert record["passed"] is False
        
    assert result["final_verification"]["stage"] == "mismatch"
    assert result["final_verification"]["passed"] is False