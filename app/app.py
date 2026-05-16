"""
EchoChamber Studio — app.py
===========================
A simulation of discursive bubbles using Romanian political comments.
Each "agent" responds from the perspective of its own political community.

This file is intentionally kept simple and well-commented.
Sociology students: you don't need to understand every line —
focus on the functions that interest you and modify them freely.

Structure:
  1. IMPORTS & SETUP
  2. DESIGN CONSTANTS  (colors, fonts, HTML templates)
  3. HELPER FUNCTIONS  (fetch article, neutral summary, etc.)
  4. TAB 1 — Agents   (all agents respond to same stimulus)
  5. TAB 2 — News     (load article → summarize → chat)
  6. TAB 3 — Debate   (agentic thread with LLM router)
  7. BUILD UI          (assemble the Gradio interface)
  8. LAUNCH
"""

# ─────────────────────────────────────────────────────────────────────────────
# 1. IMPORTS & SETUP
# ─────────────────────────────────────────────────────────────────────────────
import os

from dotenv import load_dotenv
from openai import OpenAI

# import configuration
from core.config import (
    PROVIDER_PRINCIPAL,
    MODEL_PRINCIPAL,
    PROVIDER_FALLBACK,
    MODEL_FALLBACK,
    TEMPERATURE,
    GEMINI_BASE_URL,
    OPENROUTER_BASE_URL
)

# load local environment variables
load_dotenv()

# API keys from .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Gemini client
gemini_client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url=GEMINI_BASE_URL
)

# OpenRouter client
openrouter_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL
)


# ─────────────────────────────────────────────────────────────────────────────
# 2. SIMPLE MODEL ROUTER
# ─────────────────────────────────────────────────────────────────────────────

def ask_model(prompt):
    """
    Sends a prompt to the main model.
    If the main model fails, tries the fallback model.
    """

    try:

        print("\n" + "=" * 60)
        print(f"Using MAIN provider: {PROVIDER_PRINCIPAL}")
        print(f"Using MAIN model: {MODEL_PRINCIPAL}")
        print(f"Temperature: {TEMPERATURE}")
        print("=" * 60)

        response = gemini_client.chat.completions.create(
            model=MODEL_PRINCIPAL,
            temperature=TEMPERATURE,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as main_error:

        print("\nMain model failed.")
        print(main_error)

        print("\nTrying fallback model...")

        try:

            print("\n" + "=" * 60)
            print(f"Using FALLBACK provider: {PROVIDER_FALLBACK}")
            print(f"Using FALLBACK model: {MODEL_FALLBACK}")
            print(f"Temperature: {TEMPERATURE}")
            print("=" * 60)

            response = openrouter_client.chat.completions.create(
                model=MODEL_FALLBACK,
                temperature=TEMPERATURE,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response.choices[0].message.content

        except Exception as fallback_error:

            return f"\nFallback model also failed:\n{fallback_error}"


# ─────────────────────────────────────────────────────────────────────────────
# 3. TERMINAL TEST APP
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    print("\nEchoChamber Studio — Minimal App")
    print("-" * 40)

    user_prompt = input("\nWrite your prompt:\n> ")

    result = ask_model(user_prompt)

    print("\nMODEL RESPONSE:\n")
    print(result)