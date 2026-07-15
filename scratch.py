import time
from src.languages import get_language_profile
from src.verifier import verify

# 1. Kode Python Asli dari Senior (Ground Truth)
python_code = """
import time

def calculate(iterations, param1, param2):
    result = 1.0
    for i in range(1, iterations+1):
        j = i * param1 - param2
        result -= (1/j)
        j = i * param1 + param2
        result += (1/j)
    return result

start_time = time.time()
result = calculate(200_000_000, 4, 1) * 4
end_time = time.time()

print(f"Result: {result:.12f}")
"""

# 2. Transpilasi Manual C++ (Pura-pura Hasil LLM)
# Menggunakan double untuk presisi dan std::setprecision(12) untuk format output
generated_code_cpp = """#include <iostream>
#include <iomanip>

double calculate(long long iterations, double param1, double param2) {
    float result = 1.0;
    for (long long i = 1; i <= iterations; ++i) {
        float j = i * param1 - param2;
        result -= (1.0 / j);
        j = i * param1 + param2;
        result += (1.0 / j);
    }
    return result;
}

int main() {
    // Jalankan kalkulasi dengan parameter yang sama dengan Python
    double result = calculate(200000000, 4.0, 1.0) * 4.0;
    
    // Set presisi output agar sama dengan Python (12 digit desimal)
    std::cout << std::fixed << std::setprecision(12);
    std::cout << "Result: " << result << std::endl;
    
    return 0;
}
"""

if __name__ == "__main__":
    print("=== Menjalankan Uji Coba End-to-End Manual ===")
    
    # Ambil profil bahasa C++ statis dari registry
    cpp_profile = get_language_profile("cpp")
    
    # Jalankan verifikasi (Gunakan toleransi standar 1e-6)
    print("Sedang memproses verifikasi (mohon tunggu, Python & C++ sedang berhitung)...")
    start = time.time()
    verification_result = verify(
        python_code=python_code,
        generated_code=generated_code_cpp,
        language_profile=cpp_profile,
        tolerance=1e-6
    )
    end = time.time()
    
    print(f"\nProses selesai dalam {end - start:.2f} detik.")
    print("Hasil return dari fungsi verify():")
    import pprint
    pprint.pprint(verification_result)