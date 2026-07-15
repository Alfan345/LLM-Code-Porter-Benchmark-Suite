import pytest
from unittest.mock import MagicMock
from languages import get_language_profile
from porter import port_with_self_correction

# =====================================================================
# SKENARIO 1: SUKSES PADA ATTEMPT PERTAMA (SEKALI JALAN)
# =====================================================================
def test_port_succeeds_on_first_attempt():
    """
    Memastikan loop langsung berhenti dan sukses jika panggilan pertama ke LLM
    menghasilkan kode C++ yang valid dan memiliki output yang cocok.
    """
    # Siapkan data input minimal (fungsi tambah sederhana agar kompilasi cepat)
    python_code = "print('Result:', 5 + 5)"
    cpp_profile = get_language_profile("cpp")
    
    # 1. Buat satu mock response yang langsung benar
    mock_response = MagicMock()
    mock_response.choices[0].message.content = """#include <iostream>
int main() {
    std::cout << "Result: 10" << std::endl;
    return 0;
}"""
    mock_response.usage.prompt_tokens = 40
    mock_response.usage.completion_tokens = 15
    mock_response.usage.total_tokens = 55
    
    # 2. Susun client palsu dengan return_value tunggal
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    
    # 3. Panggil fungsi orchestrator porter yang di-test
    result = port_with_self_correction(
        client=mock_client, 
        model="fake-free-model", 
        python_code=python_code, 
        language_profile=cpp_profile, 
        max_attempts=3
    )
    
    # 4. Validasi Hasil (Assertion)
    assert result["success"] is True
    assert result["attempts_needed"] == 1
    assert result["total_usage"]["total_tokens"] == 55
    
    assert len(result["history"]) == 1
    assert result["history"][0]["stage"] == "success"
    assert result["history"][0]["passed"] is True


# =====================================================================
# SKENARIO 2: SELF-CORRECTION LOOP BERHASIL SETELAH RETRY
# =====================================================================
def test_self_correction_succeeds_on_retry():
    """
    Memastikan jika attempt pertama gagal compile (typo), agen pintar kita
    mengirim feedback ke LLM, melakukan retry, dan berhasil di attempt kedua.
    """
    # Siapkan data input minimal
    python_code = "print('Result:', 5 + 5)"
    cpp_profile = get_language_profile("cpp")
    
    # 1. Buat 2 objek mock response berbeda untuk mensimulasikan kronologi
    
    # Panggilan 1: Kode C++ yang cacat sintaks (Kurang titik koma agar gagal compile)
    mock_response_fail = MagicMock()
    mock_response_fail.choices[0].message.content = """#include <iostream>
int main() {
    std::cout << "Result: 10" << std::endl // <- TYPO: Sengaja dibuat fail
    return 0;
}"""
    mock_response_fail.usage.prompt_tokens = 50
    mock_response_fail.usage.completion_tokens = 20
    mock_response_fail.usage.total_tokens = 70
    
    # Panggilan 2: Kode C++ yang diperbaiki dan valid
    mock_response_success = MagicMock()
    mock_response_success.choices[0].message.content = """#include <iostream>
int main() {
    std::cout << "Result: 10" << std::endl;
    return 0;
}"""
    mock_response_success.usage.prompt_tokens = 100
    mock_response_success.usage.completion_tokens = 25
    mock_response_success.usage.total_tokens = 125
    
    # 2. Susun client palsu dengan properti side_effect berupa list berurutan
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [mock_response_fail, mock_response_success]
    
    # 3. Jalankan fungsi agentic loop porter
    result = port_with_self_correction(
        client=mock_client, 
        model="fake-free-model", 
        python_code=python_code, 
        language_profile=cpp_profile, 
        max_attempts=3
    )
    
    # 4. Validasi Hasil (Assertion)
    assert result["success"] is True
    assert result["attempts_needed"] == 2
    
    # Total akumulasi token: 70 + 125 = 195 tokens
    assert result["total_usage"]["total_tokens"] == 195 
    
    # Memastikan riwayat perjalanan terekam runtut
    assert len(result["history"]) == 2
    assert result["history"][0]["stage"] == "compile"  # Nyata: gagal dikompilasi g++
    assert result["history"][0]["passed"] is False
    assert result["history"][1]["stage"] == "success"  # Nyata: sukses dikompilasi g++ & output match
    assert result["history"][1]["passed"] is True

# =====================================================================
# SKENARIO 3: GAGAL TOTAL (MAX ATTEMPTS HABIS KARENA MISMATCH TERUS)
# =====================================================================
def test_self_correction_fails_permanently():
    """
    Memastikan jika LLM terus-menerus memberikan jawaban yang salah (mismatch)
    sampai batas max_attempts habis, sistem berhenti dengan success=False
    dan merekam seluruh riwayat percobaan secara lengkap.
    """
    # Siapkan data input minimal yang pasti memicu mismatch logika output
    python_code = "print('Result: 100')"
    cpp_profile = get_language_profile("cpp")
    
    # 1. Buat 3 objek mock response terpisah untuk menghindari efek mutabilitas referensi
    # Semua sengaja dikasih output "Result: 999" agar verifier mendeteksi mismatch
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
        
    # 2. Susun client palsu dengan side_effect berisi list 3 objek gagal tersebut
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = responses
    
    # 3. Jalankan fungsi dengan max_attempts di-set keras ke angka 3
    result = port_with_self_correction(
        client=mock_client, 
        model="fake-free-model", 
        python_code=python_code, 
        language_profile=cpp_profile, 
        max_attempts=3
    )
    
    # 4. Validasi Hasil (Assertion Skenario 3)
    # Harus False karena tidak pernah berhasil menyamai output Python
    assert result["success"] is False
    
    # Memastikan loop berjalan penuh sebanyak 3 kali percobaan
    assert result["attempts_needed"] == 3
    assert len(result["history"]) == 3
    
    # Akumulasi token dari 3 kali percobaan: 80 * 3 = 240 tokens
    assert result["total_usage"]["total_tokens"] == 240
    
    # Memastikan semua percobaan terekam dengan stage "mismatch" secara konsisten
    for record in result["history"]:
        assert record["stage"] == "mismatch"
        assert record["passed"] is False
        
    # Memastikan data final_verification diambil dari kebenaran mutlak history terakhir
    assert result["final_verification"]["stage"] == "mismatch"
    assert result["final_verification"]["passed"] is False