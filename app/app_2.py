"""
EchoChamber Studio — app_2.py
=============================

Aplicație Gradio cu structură pe modelul profesorului,
dar cu tema, denumirile și informațiile din demo-ul proiectului.

Taburi:
1. Chat
2. Agent
3. Toți agenții
4. Dezbatere
"""

# ─────────────────────────────────────────────────────────────────────────────
# 1. IMPORTS & SETUP
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import html
from pathlib import Path

import gradio as gr
import yaml

from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from core.agent import generate_agent_response
from core.graph import run_thread

from core.config import (
    MODEL_PRINCIPAL,
    MODEL_FALLBACK,
    TEMPERATURE,
    GEMINI_BASE_URL,
    OPENROUTER_BASE_URL,
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. API CLIENTS
# ─────────────────────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

gemini_client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url=GEMINI_BASE_URL,
)

openrouter_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
)

# ─────────────────────────────────────────────────────────────────────────────
# 3. PATHS & AGENT CONFIG
# ─────────────────────────────────────────────────────────────────────────────

ROLES_PATH = PROJECT_ROOT / "assets" / "roles" / "roles.yaml"

HANDLES = {
    "anti_sistem": "@ImpotrivaSistemului",
    "conspirationist": "@AdevarulAscuns",
    "anti_populist": "@StopPopulism",
    "personalist_salvator": "@SalvatorulDeServiciu",
    "pro_european": "Pro-european",
}

PREFERRED_AGENT_ORDER = [
    "anti_sistem",
    "conspirationist",
    "personalist_salvator",
    "pro_european",
    "anti_populist",
]

# Pro-european rămâne în app, dar nu este bifat implicit,
# pentru că ai spus că nu ai vectorstore pentru el.
DEFAULT_DEBATE_AGENTS = [
    "anti_sistem",
    "conspirationist",
    "personalist_salvator",
    "anti_populist",
]

# ─────────────────────────────────────────────────────────────────────────────
# 4. LOAD AVAILABLE AGENTS
# ─────────────────────────────────────────────────────────────────────────────

def load_agent_info():
    """
    Citește informațiile agenților din assets/roles/roles.yaml.
    Acceptă atât formatul:
        agents:
          anti_sistem: ...
    cât și:
        anti_sistem: ...
    """
    if not ROLES_PATH.exists():
        return {}

    with open(ROLES_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data.get("agents", data)


def load_agent_choices():
    """
    Returnează slug-urile agenților în ordinea preferată.
    """
    roles = load_agent_info()
    existing_slugs = list(roles.keys())

    ordered = [slug for slug in PREFERRED_AGENT_ORDER if slug in existing_slugs]

    for slug in existing_slugs:
        if slug not in ordered:
            ordered.append(slug)

    return ordered


agent_info = load_agent_info()
agent_choices = load_agent_choices()


def agent_display_name(slug):
    """
    Creează eticheta afișată în dropdown-uri / checkbox-uri.
    Folosește emoji și name din YAML, iar dacă lipsesc, folosește HANDLES.
    """
    info = agent_info.get(slug, {})
    emoji = info.get("emoji", "")
    name = info.get("name", HANDLES.get(slug, slug))

    return f"{emoji} {name}".strip()


AGENTS = [(agent_display_name(slug), slug) for slug in agent_choices]

DEFAULT_AGENT = (
    "personalist_salvator"
    if "personalist_salvator" in agent_choices
    else agent_choices[0]
    if agent_choices
    else None
)

DEFAULT_SELECTED_DEBATE_AGENTS = [
    slug for slug in DEFAULT_DEBATE_AGENTS if slug in agent_choices
]

# ─────────────────────────────────────────────────────────────────────────────
# 5. SIMPLE MODEL ROUTER
# ─────────────────────────────────────────────────────────────────────────────

def ask_model(prompt):
    """
    Sends a prompt to the main model.
    If the main model fails, tries the fallback model.
    """
    if not prompt or not prompt.strip():
        return "Scrie un prompt."

    try:
        response = gemini_client.chat.completions.create(
            model=MODEL_PRINCIPAL,
            temperature=TEMPERATURE,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
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
                        "content": prompt,
                    }
                ],
            )
            return response.choices[0].message.content

        except Exception as fallback_error:
            return f"\nFallback model also failed:\n{fallback_error}"

# ─────────────────────────────────────────────────────────────────────────────
# 6. CHAT FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def chat(prompt):
    if not prompt or not prompt.strip():
        return "Scrie un prompt."

    return ask_model(prompt)

# ─────────────────────────────────────────────────────────────────────────────
# 7. AGENT RAG FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def rag_agent_response(stimulus, agent_slug, provider, k):
    if not agent_slug:
        return "Nu există agenți în assets/roles/roles.yaml.", ""

    if not stimulus or not stimulus.strip():
        return "Scrie un text politic pentru agent.", ""

    try:
        result = generate_agent_response(
            agent_slug=agent_slug,
            stimulus=stimulus,
            provider=provider,
            k=int(k),
            temperature=0.3,
            roles_path=str(ROLES_PATH),
        )

        return result.get("response", ""), result.get("rag_text", "")

    except Exception as e:
        return f"[Eroare Agent RAG: {type(e).__name__} — {e}]", ""

# ─────────────────────────────────────────────────────────────────────────────
# 8. ALL AGENTS FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def all_agents_response(stimulus, provider, k):
    """
    Trimite același text politic către toți agenții definiți în roles.yaml.
    """
    if not stimulus or not stimulus.strip():
        return "Scrie un text politic."

    if not agent_choices:
        return "Nu există agenți în assets/roles/roles.yaml."

    sections = []

    for slug in agent_choices:
        info = agent_info.get(slug, {})
        emoji = info.get("emoji", "")
        name = info.get("name", HANDLES.get(slug, slug))

        try:
            result = generate_agent_response(
                agent_slug=slug,
                stimulus=stimulus,
                provider=provider,
                k=int(k),
                temperature=0.3,
                roles_path=str(ROLES_PATH),
            )

            response_text = result.get("response", "")

        except Exception as e:
            response_text = f"[Eroare: {type(e).__name__} — {e}]"

        sections.append(f"### {emoji} {name}\n\n{response_text}")

    return "\n\n---\n\n".join(sections)

# ─────────────────────────────────────────────────────────────────────────────
# 9. DISPLAY FUNCTION FOR DEBATE
# ─────────────────────────────────────────────────────────────────────────────

def render_thread_html(messages, agent_info):
    cards = []

    for msg in messages:
        slug = str(msg.get("slug", ""))
        agent = html.escape(str(msg.get("agent", "")))
        handle = html.escape(str(msg.get("handle", HANDLES.get(slug, slug))))
        text = html.escape(str(msg.get("text", "")))
        turn = msg.get("turn", "")

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
# 10. RUN MULTI-AGENT THREAD
# ─────────────────────────────────────────────────────────────────────────────

def run_multi_agent_thread(stimulus, provider, total_turns, selected_agents):
    if not stimulus or not stimulus.strip():
        return "Scrie un text politic mai întâi."

    if not selected_agents:
        return "Selectează cel puțin un agent."

    if len(selected_agents) < 2:
        return "Selectează cel puțin doi agenți pentru dezbatere."

    try:
        messages = run_thread(
            stimulus=stimulus,
            active_slugs=selected_agents,
            total_turns=int(total_turns),
            provider=provider,
            k=3,
        )

        current_agent_info = load_agent_info()
        return render_thread_html(messages, current_agent_info)

    except Exception as e:
        return f"[Eroare Multi-agent Thread: {type(e).__name__} — {e}]"

# ─────────────────────────────────────────────────────────────────────────────
# 11. THEME
# ─────────────────────────────────────────────────────────────────────────────

THEME = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="sky",
    neutral_hue="slate",
    radius_size="lg",
    spacing_size="lg",
    text_size="md",
    font=[
        gr.themes.GoogleFont("Inter"),
        "system-ui",
        "sans-serif",
    ],
    font_mono=[
        gr.themes.GoogleFont("JetBrains Mono"),
        "monospace",
    ],
)

HEADER = """
# EchoChamber Studio
**Simulare a bulelor discursive folosind comentarii politice**

*Aplicație prototip cu scopuri educationale si de cercetare. Agenții sunt roluri simulate, nu persoane reale.*
"""

DISCLAIMER = """
---
**Ethics & limitations**

EchoChamber este un prototip experimental-educațional și de cercetare. Agenții sunt roluri discursive simulate, 
**nu** persoane reale sau reprezentanți ai unor grupuri sociale reale. Răspunsurile generate pot conține 
părtinire, exagerări sau afirmații incorecte și trebuie interpretate ca atare.
"""

# ─────────────────────────────────────────────────────────────────────────────
# 12. INTERFACES / TABS
# ─────────────────────────────────────────────────────────────────────────────

tab_chat = gr.Interface(
    fn=chat,
    title="Chat",
    description="Chat simplu cu modelul principal.",
    inputs=gr.Textbox(
        label="Prompt",
        value="Explică în 2 propoziții ce este un LLM.",
        lines=4,
    ),
    outputs=gr.Textbox(
        label="Răspuns",
        lines=8,
    ),
    submit_btn="Trimite",
    flagging_mode="never",
)

tab_agent = gr.Interface(
    fn=rag_agent_response,
    title="Agent",
    description="Un agent RAG răspunde la un text politic folosind contextul recuperat din bula sa discursivă.",
    inputs=[
        gr.Textbox(
            label="Text politic (știre sau comentariu)",
            value="CCR a decis anularea alegerilor după suspiciuni privind influențe externe.",
            lines=4,
        ),
        gr.Dropdown(
            choices=AGENTS,
            value=DEFAULT_AGENT,
            label="Selectează agentul",
        ),
        gr.Dropdown(
            choices=["gemini", "deepseek"],
            value="gemini",
            label="Provider",
        ),
        gr.Slider(
            minimum=1,
            maximum=10,
            value=5,
            step=1,
            label="Număr fragmente recuperate (k)",
        ),
    ],
    outputs=[
        gr.Textbox(
            label="Răspuns agent",
            lines=8,
        ),
        gr.Textbox(
            label="Context recuperat din bula discursivă",
            lines=12,
        ),
    ],
    submit_btn="Generează răspuns RAG",
    flagging_mode="never",
)

tab_all = gr.Interface(
    fn=all_agents_response,
    title="Toți agenții",
    description="Același text politic este trimis pe rând tuturor agenților definiți în roles.yaml.",
    inputs=[
        gr.Textbox(
            label="Subiect / text politic",
            value="Alegeri anticipate Cehia",
            lines=4,
        ),
        gr.Dropdown(
            choices=["gemini", "deepseek"],
            value="gemini",
            label="Provider",
        ),
        gr.Slider(
            minimum=1,
            maximum=10,
            value=5,
            step=1,
            label="Număr fragmente recuperate (k)",
        ),
    ],
    outputs=gr.Markdown(label="Răspunsuri generate"),
    submit_btn="Submit",
    clear_btn="Clear",
    flagging_mode="never",
)

tab_debate = gr.Interface(
    fn=run_multi_agent_thread,
    title="Dezbatere",
    description="Simulează o conversație între mai mulți agenți discursivi.",
    inputs=[
        gr.Textbox(
            label="Text politic",
            value="România are nevoie de un lider puternic care să nu mai asculte de Bruxelles.",
            lines=4,
        ),
        gr.Dropdown(
            choices=["gemini", "deepseek"],
            value="deepseek",
            label="Provider",
        ),
        gr.Slider(
            minimum=2,
            maximum=8,
            value=4,
            step=1,
            label="Număr total de intervenții",
        ),
        gr.CheckboxGroup(
            choices=AGENTS,
            value=DEFAULT_SELECTED_DEBATE_AGENTS,
            label="Selectează agenții participanți",
        ),
    ],
    outputs=gr.HTML(label="Conversație generată"),
    submit_btn="Pornește dezbaterea",
    flagging_mode="never",
)

TABS = [
    ("Chat", tab_chat),
    ("Agent", tab_agent),
    ("Toți agenții", tab_all),
    ("Dezbatere", tab_debate),
]

# ─────────────────────────────────────────────────────────────────────────────
# 13. BUILD UI
# ─────────────────────────────────────────────────────────────────────────────

with gr.Blocks(title="EchoChamber Studio", theme=THEME) as demo:

    gr.Markdown(HEADER)

    with gr.Tabs():
        for tab_name, interface in TABS:
            with gr.Tab(tab_name):
                interface.render()

    gr.Markdown(DISCLAIMER)

# ─────────────────────────────────────────────────────────────────────────────
# 14. LAUNCH
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = os.getenv("GRADIO_SERVER_PORT")

    demo.launch(
        server_name="127.0.0.1",
        server_port=int(port) if port else None,
        share=True,
        inbrowser=True,
    )