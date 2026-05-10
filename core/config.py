# core/config.py
# ===============
# Central configuration: loads roles.yaml and .env API keys.
# All other modules import from here instead of reading files directly.
#
# Students: you don't need to modify this file.
# If you want to add a new LLM provider, add it to AVAILABLE_MODELS below.

PROVIDER_PRINCIPAL = "gemini"

MODEL_PRINCIPAL = "gemini-2.5-flash-lite"

PROVIDER_FALLBACK = "openrouter"

MODEL_FALLBACK = "openai/gpt-3.5-turbo"

TEMPERATURE = 0.2


# API endpoints

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"