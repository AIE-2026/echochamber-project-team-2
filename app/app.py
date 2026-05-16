"""
EchoChamber Studio — app.py
===========================

Minimal app with:
1. Simple chat tab
2. Agent RAG tab
"""

# ─────────────────────────────────────────────────────────────────────────────
# 1. IMPORTS & SETUP
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
from pathlib import Path

import gradio as gr
import yaml

from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from core.agent import generate_agent_response

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

PROJECT_ROOT = Path(__file__).resolve().parent.parent

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

        try:

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
# 3. SIMPLE CHAT FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def chat(prompt):

    if not prompt.strip():
        return "Scrie un prompt."

    return ask_model(prompt)


# ─────────────────────────────────────────────────────────────────────────────
# 4. LOAD AVAILABLE AGENTS
# ─────────────────────────────────────────────────────────────────────────────

def load_agent_choices():

    roles_path = PROJECT_ROOT / "assets" / "roles" / "roles.yaml"

    if not roles_path.exists():
        return []

    with open(roles_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    roles = data["agents"] if "agents" in data else data

    return list(roles.keys())


# ─────────────────────────────────────────────────────────────────────────────
# 5. RAG AGENT FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def rag_agent_response(agent_slug, stimulus, provider, k):

    if not agent_slug:
        return "Nu există agenți în assets/roles/roles.yaml.", ""

    if not stimulus.strip():
        return "Scrie un text politic pentru agent.", ""

    try:

        result = generate_agent_response(
            agent_slug=agent_slug,
            stimulus=stimulus,
            provider=provider,
            k=int(k),
            temperature=0.3,
            roles_path="assets/roles/roles.yaml",
        )

        return result["response"], result["rag_text"]

    except Exception as e:

        return f"[Eroare Agent RAG: {type(e).__name__} — {e}]", ""


# ─────────────────────────────────────────────────────────────────────────────
# 6. BUILD UI
# ─────────────────────────────────────────────────────────────────────────────

agent_choices = load_agent_choices()

with gr.Blocks(title="EchoChamber") as demo:

    gr.Markdown("# EchoChamber")
    gr.Markdown("Aplicație minimă pentru testarea modelelor și a agenților RAG.")

    # ─────────────────────────────────────────────────────────────────────
    # TAB 1 — SIMPLE CHAT
    # ─────────────────────────────────────────────────────────────────────

    with gr.Tab("Chat simplu"):

        prompt_box = gr.Textbox(
            label="Prompt",
            value="Explică în 2 propoziții ce este un LLM.",
            lines=4
        )

        chat_button = gr.Button("Trimite")

        chat_output = gr.Textbox(
            label="Răspuns",
            lines=8
        )

        chat_button.click(
            fn=chat,
            inputs=prompt_box,
            outputs=chat_output
        )

    # ─────────────────────────────────────────────────────────────────────
    # TAB 2 — AGENT RAG
    # ─────────────────────────────────────────────────────────────────────

    with gr.Tab("Agent RAG"):

        agent_dropdown = gr.Dropdown(
            choices=agent_choices,
            value=agent_choices[0] if agent_choices else None,
            label="Agent"
        )

        provider_dropdown = gr.Dropdown(
            choices=["gemini", "deepseek"],
            value="gemini",
            label="Provider"
        )

        stimulus_box = gr.Textbox(
            label="Text politic nou",
            value="CCR a decis anularea alegerilor după suspiciuni privind influențe externe.",
            lines=4
        )

        k_slider = gr.Slider(
            minimum=1,
            maximum=10,
            value=5,
            step=1,
            label="Număr fragmente recuperate"
        )

        agent_button = gr.Button("Generează răspuns RAG")

        agent_response_box = gr.Textbox(
            label="Răspuns agent",
            lines=8
        )

        context_box = gr.Textbox(
            label="Context recuperat",
            lines=12
        )

        agent_button.click(
            fn=rag_agent_response,
            inputs=[
                agent_dropdown,
                stimulus_box,
                provider_dropdown,
                k_slider
            ],
            outputs=[
                agent_response_box,
                context_box
            ]
        )


# ─────────────────────────────────────────────────────────────────────────────
# 7. LAUNCH
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo.launch()