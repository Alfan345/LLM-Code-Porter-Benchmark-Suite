import sys
import os

# Register the src folder into the system path for module lookups
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Import the original build_ui function from src/app.py
from app import build_ui

if __name__ == "__main__":
    ui = build_ui()
    # Fix: Remove custom server_name and server_port configurations.
    # Let Hugging Face Spaces handle the default routing parameters natively for Gradio 5.
    ui.launch()