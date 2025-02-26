import subprocess
import sys
import os

# Path to your virtual environment's Python executable
venv_python = os.path.join("venv", "Scripts", "python.exe")

# scripts = ["sec_links_scrapper.py", "sec_scrapper.py", "yahoo_scrapper.py", "web_search.py", "openai/assistant_handler.py", "openai/summarizer.py"]
scripts = ["openai/assistant_handler.py", "openai/summarizer.py"]

# scripts = ["openai/summarizer.py"]

for script in scripts:
    print(f"Running {script}...")
    subprocess.run([venv_python, script], check=True)
    print(f"Finished {script}\n")


# MeridianLink Inc. (MLNK),PagerDuty Inc. (PD),Amplitude Inc. (AMPL),CompoSecure Inc. (CMPO),Weave Communications Inc. (WEAV),VNET Group Inc. (VNET),8x8 Inc. (EGHT)
# asst_315HKrr8B1WllqOojQXSijrp