import os
from pathlib import Path

from shared.config import load_env

load_env(Path(__file__).parent.parent / ".env")

API_KEY = os.environ["CLOCKIFY_API_KEY"]
WORKSPACE_ID = os.environ["CLOCKIFY_WORKSPACE_ID"]
BASE_URL = "https://api.clockify.me/api/v1"
HEADERS = {"X-Api-Key": API_KEY}
