from pathlib import Path

from dotenv import load_dotenv


def load_env(env_file: Path | None = None) -> None:
    found = load_dotenv(dotenv_path=env_file)
    if not found:
        path_hint = str(env_file) if env_file else ".env (searched from cwd)"
        raise FileNotFoundError(f".env file not found: {path_hint}")
