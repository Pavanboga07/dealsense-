"""Config: loads the SerpApi key from the environment, fails loudly if missing.

The python-dotenv import is lazy so the package stays importable (and
testable) on machines where only the fixture tests run.
"""

import os


def _load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # .env loading is a convenience; env vars still work


def serpapi_key() -> str:
    _load_env()
    key = os.environ.get("SERPAPI_API_KEY", "").strip()
    if not key or key == "your_key_here":
        raise RuntimeError(
            "SERPAPI_API_KEY is not set. Copy .env.example to .env and add "
            "your free key from https://serpapi.com"
        )
    return key
