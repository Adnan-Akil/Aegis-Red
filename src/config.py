import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
ROOT_DIR = Path(__file__).parent.parent

# Load environment variables
# Prioritize the main .env if it exists, otherwise use the benchmark app one
main_env = ROOT_DIR / ".env"
if main_env.exists():
    load_dotenv(main_env)
else:
    # Fallback for the current benchmark setup
    load_dotenv(ROOT_DIR / "benchmark_apps" / "chatbot_vuln" / "backend" / ".env")

# LLM Configurations
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
REPORT_LLM_API_KEY = os.getenv("REPORT_LLM_API_KEY")
DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Database Configuration
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "framework.db"

# Agent Parameters
MAX_ITERATIONS = 5
MAX_MUTATIONS = 2

# Browser Settings
HEADLESS = True
BROWSER_TIMEOUT = 30000
