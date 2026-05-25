"""
EchoChamber Studio — app.py
===========================

Minimal app with:
1. Simple chat tab
2. Agent RAG tab
3. Multi-agent thread tab
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

from core.graph import run_thread
import html

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

def load_agent_info():
    """Load full agent information from roles.yaml"""
    roles_path = PROJECT_ROOT / "assets" / "roles" / "roles.yaml"

    if not roles_path.exists():
        return {}

    with open(roles_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    roles = data["agents"] if "agents" in data else data
    return roles

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
# 6. DISPLAY FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def render_thread_html(messages, agent_info):
    cards = []

    for msg in messages:
        agent = html.escape(str(msg.get("agent", "")))
        slug = str(msg.get("slug", ""))
        handle = html.escape(str(msg.get("handle", msg.get("slug", ""))))
        text = html.escape(str(msg.get("text", "")))
        turn = msg.get("turn", "")

        # Get agent color and emoji from agent_info if available
        color = "#e05a35"
        emoji = ""
        if slug in agent_info:
            color = agent_info[slug].get("color", "#e05a35")
            emoji = agent_info[slug].get("emoji", "")

        cards.append(f"""
        <div style='
            border-left:3px solid {color};
            padding:.7rem 1rem;
            margin:.5rem 0;
            background:#f5f0e8;
            border-radius:8px;
        '>
            <div style='
                font-size:.75rem;
                color:{color};
                text-transform:uppercase;
                font-weight:600;
            '>
                {emoji} {agent}
            </div>
            <div style='
                font-size:.7rem;
                color:#888;
                margin-bottom:.35rem;
            '>
                {handle} · Turn {turn}
            </div>
            <div style='
                color:#333;
                line-height:1.5;
            '>
                {text}
            </div>
        </div>
        """)

    return "\n".join(cards)

# ─────────────────────────────────────────────────────────────────────────────
# 7. RUN MULTI-AGENT THREAD
# ─────────────────────────────────────────────────────────────────────────────

def run_multi_agent_thread(stimulus, provider, total_turns, 
                           use_anti_sistem, use_conspirationist, 
                           use_personalist_salvator, use_pro_european, 
                           use_anti_populist):
    
    active_slugs = []

    if use_anti_sistem:
        active_slugs.append("anti_sistem")
    if use_conspirationist:
        active_slugs.append("conspirationist")
    if use_personalist_salvator:
        active_slugs.append("personalist_salvator")
    if use_pro_european:
        active_slugs.append("pro_european")
    if use_anti_populist:
        active_slugs.append("anti_populist")

    if not stimulus.strip():
        return "Scrie un text politic mai întâi."

    if not active_slugs:
        return "Selectează cel puțin un agent."

    try:
        messages = run_thread(
            stimulus=stimulus,
            active_slugs=active_slugs,
            total_turns=int(total_turns),
            provider=provider,
            k=3,
        )
        agent_info = load_agent_info()
        return render_thread_html(messages, agent_info)

    except Exception as e:
        return f"[Eroare Multi-agent Thread: {type(e).__name__} — {e}]"

# ─────────────────────────────────────────────────────────────────────────────
# 8. BUILD UI
# ─────────────────────────────────────────────────────────────────────────────

agent_choices = load_agent_choices()
agent_info = load_agent_info()

# Create agent labels with emoji for dropdown
agent_labels = []
for slug in agent_choices:
    if slug in agent_info:
        emoji = agent_info[slug].get("emoji", "")
        name = agent_info[slug].get("name", slug)
        agent_labels.append(f"{emoji} {name}")
    else:
        agent_labels.append(slug)

with gr.Blocks(title="EchoChamber Studio", theme=gr.themes.Soft()) as demo:

    gr.Markdown("""
    # EchoChamber Studio
    **Simulare a bulelor discursive folosind comentarii politice**
    
    *Aplicație prototip pentru cercetare și educație. Agenții sunt roluri simulate, nu persoane reale.*
    """)

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
            label="Selectează agentul"
        )

        provider_dropdown = gr.Dropdown(
            choices=["gemini", "deepseek"],
            value="gemini",
            label="Provider"
        )

        stimulus_box = gr.Textbox(
            label="Text politic (știre sau comentariu)",
            value="CCR a decis anularea alegerilor după suspiciuni privind influențe externe.",
            lines=4
        )

        k_slider = gr.Slider(
            minimum=1,
            maximum=10,
            value=5,
            step=1,
            label="Număr fragmente recuperate (k)"
        )

        agent_button = gr.Button("Generează răspuns RAG")

        agent_response_box = gr.Textbox(
            label="Răspuns agent",
            lines=8
        )

        context_box = gr.Textbox(
            label="Context recuperat din bula discursivă",
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

    # ─────────────────────────────────────────────────────────────────────
    # TAB 3 — MULTI-AGENT THREAD
    # ─────────────────────────────────────────────────────────────────────

    with gr.Tab("Dezbatere multi-agent"):

        gr.Markdown("""
        ### Simulează o conversație între mai mulți agenți discursivi
        
        Selectează agenții care vor participa la dezbatere și vezi cum reacționează fiecare la același text politic.
        """)

        thread_stimulus = gr.Textbox(
            label="Text politic",
            value="România are nevoie de un lider puternic care să nu mai asculte de Bruxelles.",
            lines=4
        )

        thread_provider = gr.Dropdown(
            choices=["gemini", "deepseek"],
            value="deepseek",
            label="Provider"
        )

        thread_turns = gr.Slider(
            minimum=2,
            maximum=8,
            value=4,
            step=1,
            label="Număr total de intervenții"
        )

        gr.Markdown("### Selectează agenții participanți")

        # Get agent display names with emoji from YAML
        anti_sistem_label = f"{agent_info.get('anti_sistem', {}).get('emoji', '')} Anti-sistem ({agent_info.get('anti_sistem', {}).get('name', '@ImpotrivaSistemului')})"
        conspirationist_label = f"{agent_info.get('conspirationist', {}).get('emoji', '')} Conspiraționist ({agent_info.get('conspirationist', {}).get('name', 'Conspiraționist')})"
        personalist_label = f"{agent_info.get('personalist_salvator', {}).get('emoji', '')} Personalist-salvator ({agent_info.get('personalist_salvator', {}).get('name', 'Personalist-salvator')})"
        pro_european_label = f"{agent_info.get('pro_european', {}).get('emoji', '')} Pro-european ({agent_info.get('pro_european', {}).get('name', 'Pro-european')})"
        anti_populist_label = f"{agent_info.get('anti_populist', {}).get('emoji', '')} Anti-populist ({agent_info.get('anti_populist', {}).get('name', 'Anti-populist')})"

        use_anti_sistem = gr.Checkbox(value=True, label=anti_sistem_label)
        use_conspirationist = gr.Checkbox(value=True, label=conspirationist_label)
        use_personalist_salvator = gr.Checkbox(value=True, label=personalist_label)
        use_pro_european = gr.Checkbox(value=True, label=pro_european_label)
        use_anti_populist = gr.Checkbox(value=True, label=anti_populist_label)

        thread_button = gr.Button("Pornește dezbaterea", variant="primary")
        thread_output = gr.HTML(label="Conversație generată")

        thread_button.click(
            fn=run_multi_agent_thread,
            inputs=[
                thread_stimulus, 
                thread_provider, 
                thread_turns, 
                use_anti_sistem, 
                use_conspirationist, 
                use_personalist_salvator,
                use_pro_european,
                use_anti_populist
            ],
            outputs=thread_output
        )

    # ─────────────────────────────────────────────────────────────────────
    # FOOTER with disclaimer
    # ─────────────────────────────────────────────────────────────────────

    gr.Markdown("""
    ---
    **Ethics & limitations**
    
    EchoChamber este un prototip experimental-educațional și de cercetare. Agenții sunt roluri discursive simulate, 
    **nu** persoane reale sau reprezentanți ai unor grupuri sociale reale. Răspunsurile generate pot conține 
    părtinire, exagerări sau afirmații incorecte și trebuie interpretate ca atare.

    """)

# ─────────────────────────────────────────────────────────────────────────────
# 9. LAUNCH
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo.launch(share=False)