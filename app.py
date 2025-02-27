import subprocess
import sys
# import os
from pathlib import Path # added this because we need to use Path to get the path to the venv's python executable

# Path to your virtual environment's Python executable
# venv_python = os.path.join("venv", "Scripts", "python.exe")
SCRIPT_DIR = Path(__file__).parent 

# scripts = ["sec_links_scrapper.py", "sec_scrapper.py", "yahoo_scrapper.py", "web_search.py", "openai/assistant_handler.py", "openai/summarizer.py"]
scripts = ["openai/assistant_handler.py", "openai/summarizer.py"]

# scripts = ["openai/summarizer.py"]

for script in scripts:
    print(f"Running {script}...")
    # subprocess.run([venv_python, script], check=True)
    script_path = SCRIPT_DIR / script

    # Added for error handling
    if not script_path.exists():
        print(f"Error: Script not found: {script_path}")
        continue

    # subprocess.run([venv_python, script], check=True) - reemoved this because we do not need venv_python if we run in a venv
    subprocess.run([sys.executable, str(script_path)], check=True)
    print(f"Finished {script}\n")


# MeridianLink Inc. (MLNK),PagerDuty Inc. (PD),Amplitude Inc. (AMPL),CompoSecure Inc. (CMPO),Weave Communications Inc. (WEAV),VNET Group Inc. (VNET),8x8 Inc. (EGHT)
# asst_315HKrr8B1WllqOojQXSijrp