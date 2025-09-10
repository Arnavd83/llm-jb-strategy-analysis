import os

def test_env_keys_presence():
    keys = [
        "OPENAI_API_KEY",
        "TOGETHER_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "HUGGING_FACE_HUB_TOKEN",
        "HF_TOKEN",
    ]
    print("=== Environment keys visible to pytest ===")
    for k in keys:
        print(f"{k} set?", bool(os.getenv(k)))
    print("=========================================")
    assert True  # This test is informational only
