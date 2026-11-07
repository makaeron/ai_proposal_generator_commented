# Import Path so we can build project-relative file paths.
from pathlib import Path

# BASE_DIR points to the project root folder.
# config.py lives inside src/, so parents[1] moves up two levels:
# config.py -> src -> project root.
BASE_DIR = Path(__file__).resolve().parents[1]

# DATA_DIR stores mock input data such as customers and products.
DATA_DIR = BASE_DIR / 'data'

# OUTPUT_DIR stores generated JSON, TXT, and HTML proposal files.
OUTPUT_DIR = BASE_DIR / 'outputs'

# Any total discount above this threshold triggers an approval flag.
APPROVAL_DISCOUNT_THRESHOLD = 15.0

# Default tax percentage used when a regional tax is not found.
DEFAULT_TAX_PCT = 13.0

# Default Ollama model name for local generation.
DEFAULT_OLLAMA_MODEL = 'mistral'

# Default Ollama HTTP endpoint for non-streaming generation.
DEFAULT_OLLAMA_URL = 'http://localhost:11434/api/generate'
