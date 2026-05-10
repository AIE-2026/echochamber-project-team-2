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

# import config
from core.config import (
    MAIN_MODEL,
    FALLBACK_MODEL,
    GEMINI_BASE_URL,
    OPENROUTER_BASE_URL
)

# load .env
load_dotenv()

# API keys
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


def ask_model(prompt):

    try:
        print(f"\nUsing MAIN model: {MAIN_MODEL}")

        response = gemini_client.chat.completions.create(
            model=MAIN_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:

        print("\nMain model failed.")
        print(e)

        print(f"\nUsing FALLBACK model: {FALLBACK_MODEL}")

        try:

            response = openrouter_client.chat.completions.create(
                model=FALLBACK_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response.choices[0].message.content

        except Exception as fallback_error:

            return f"Fallback also failed: {fallback_error}"


if __name__ == "__main__":

    user_prompt = input("\nWrite your prompt:\n> ")

    result = ask_model(user_prompt)

    print("\nMODEL RESPONSE:\n")
    print(result)