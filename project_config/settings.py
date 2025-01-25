from dotenv import load_dotenv
import os

load_dotenv()

ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))

# Load variables from .env
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

VESPA_HOST = os.environ.get("VESPA_HOST")
VESPA_PORT = os.environ.get("VESPA_PORT")

FASTAPI_HOST = os.environ.get("FASTAPI_HOST")
FASTAPI_PORT = os.environ.get("FASTAPI_PORT")

API_USERNAME = os.environ.get("API_USERNAME")
API_PASSWORD = os.environ.get("API_PASSWORD")

STREAMLIT_USERNAME = os.environ.get("STREAMLIT_USERNAME")
STREAMLIT_PASSWORD = os.environ.get("STREAMLIT_PASSWORD")

# OpenAI embedding model used for text embedding across the repository
EMBEDDING_MODEL = "text-embedding-3-large"

# Chatbot model name
CHATBOT_MODEL = "gpt-4o"

# Number of chunks used for context
NUM_OF_CONTEXT_CHUNKS = 5

# Streamlit Sessions Save Path
SESSIONS_PATH = os.path.join(ROOT_DIR, "sessions/")

TEMP_DIR = "/tmp/uploads"
