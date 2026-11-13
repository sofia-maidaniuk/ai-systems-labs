OLLAMA_BASE_URL = "http://localhost:11434/v1"
REQUEST_TIMEOUT = 180

DEFAULT_MODEL = "qwen3:4b-instruct-2507-q8_0"

MODELS = {
    "qwen3:4b-instruct-2507-q8_0": "Qwen3-4B · Q8_0",
    "qwen3:4b-instruct-2507-q4_K_M": "Qwen3-4B · Q4_K_M",
    "qwen3:4b-instruct-2507-q8-8k": "Qwen3-4B · Q8_0 · 8K",
}

TARGET_CONTEXT_TOKENS = 4096

GENERATION_PARAMS = {
    "audience": {
        "temperature": 0.2,
        "max_tokens": 3200,
    },
    "hooks": {
        "temperature": 0.5,
        "max_tokens": 2800,
    },
    "creatives": {
        "temperature": 0.4,
        "max_tokens": 700,
    },
    "revision": {
        "temperature": 0.3,
        "max_tokens": 1200,
    },
}
