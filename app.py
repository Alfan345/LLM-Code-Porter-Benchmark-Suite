import sys
import os

# Daftarkan folder src ke dalam path sistem pencarian Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Impor build_ui dari modul src/app.py yang asli
from app import build_ui

if __name__ == "__main__":
    ui = build_ui()
    # HF Spaces secara default menjalankan aplikasi di port 7860
    ui.launch(server_name="0.0.0.0", server_port=7860)