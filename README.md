# EchoChamber Studio

Simulation of discursive bubbles using political comments from YouTube and RSS feeds.  
Each agent responds from the perspective of its own political community, retrieved from a real corpus of comments. EchoChamber Studio explores how large language models can simulate different discursive perspectives when analyzing the same input text. The system allows users to input a news article or social text and observe how different agent “voices” interpret and respond to it.

## Project Overview

EchoChamber is an educational and research prototype that:
- Simulates political discourse from different ideological perspectives
- Uses RAG (Retrieval-Augmented Generation) to ground responses in real comments
- Orchestrates multi-agent debates using LangGraph workflows
- Provides a Gradio interface for interactive exploration

The application can:

    load or use a political or social news article (via URL or text input);
    summarize the input content;
    generate a response from a single selected agent;
    compare responses across multiple agents;
    simulate a short multi-agent debate based on the same input.

The goal is to provide a controlled environment for studying variation in language, framing, and interpretation.

## Why this project matters

The project explores how AI agents can be used to study discursive framing, polarization, narrative variation, and the limits of automated interpretation in political communication.

It does not measure real public opinion, but instead simulates how different interpretive positions can shape responses to the same informational input.

## Project Structure

```
echochamber/
├── notebooks/              # Weekly course notebooks (added during the semester)
├── collector/              # Scripts for collecting comments from YouTube / RSS
├── data/
│   ├── raw/                # Raw collected comments (CSV or JSONL)
│   ├── cleaned/            # Cleaned and standardized corpus
│   └── bubbles/            # One JSONL file per agent after annotation
├── assets/
│   └── roles/              # Agent role cards (roles.yaml) — written by students
├── scripts/
│   ├── clean_corpus.py     # Cleans and standardizes raw data
│   └── build_vectorstore.py # Builds FAISS vector index from data/bubbles/
├── core/                   # Core infrastructure — do not modify
│   ├── agent.py            # Agent class: reads roles.yaml + retrieves from corpus
│   ├── retriever.py        # Semantic search over FAISS index
│   ├── graph.py            # LangGraph agentic debate orchestration
│   └── metrics.py          # Dissimilarity, sentiment, and visualization
├── app/
│   └── app.py              # Gradio application (built incrementally during course)
└── reports/                # Final report and ethics checklist templates
```

## Setup | How to run locally

### Windows PowerShell

git clone <your-repo-url>
cd echochamber
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt
cp .env.example .env
python -m app.app

The application runs locally by default at http://127.0.0.1:7860

### Environment variables

Create a local .env file based on .env.example.

Do not commit .env or API keys. API keys and sensitive data must never be committed.

#### Gemini (free tier available)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite

#### DeepSeek (higher free quota)
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat


## Technical Components

| Component | Path | Description |
|-----------|------|-------------|
| Retriever | `core/retriever.py` | Searches FAISS vectorstore for relevant comments |
| Agent | `core/agent.py` | Combines role, retrieved context and LLM response |
| Graph | `core/graph.py` | Coordinates multi-agent conversation flow |
| Metrics | `core/metrics.py` | Dissimilarity, sentiment, and visualization tools |
| App | `app/app.py` | Exposes the system through a Gradio interface |

The retrieval component uses FAISS vector indexes stored under `assets/vectorstores/`. These indexes are used to retrieve similar comments for each agent and provide discursive context to the language model.

## Application Features
 #### Chat simplu
 	Ask the selected model a direct question
#### Agent RAG	
  Generate one response from a selected simulated agent
#### Multi-agent thread	
  Run a short multi-agent conversation between selected agents
  
  ### Workflow explanation

    - The input text is the central object of analysis.
    - Retrieved comments provide contextual discourse, not factual validation.
    - Agent roles define tone, perspective, and response constraints.
    - Each agent starts from a discursive role defined in YAML.
    - The retriever and RAG context remain the factual basis of the intervention.
    - Previous messages are kept in state and become part of the context.
    - The router decides when the thread continues and when the graph stops.


## Agents

| Slug | Display name | Emoji | Color | Discursive zone |
|---|---|---|---|---|
| `personalist_salvator` | Personalist-salvator | 🛡️ | #FFD54F | Conspiratorial / marginal / mythic-national |
| `anti_sistem` | @ImpotrivaSistemului | 🔍 | #2d2d2d | Official sovereignist / anti-system electoral |
| `conspirationist` | Conspiraționist | 🕵️ | #7E57C2 | Systemic distrust / alternative media |
| `pro_european` | Pro-european | 🇪🇺 | #1565C0 | Mainstream institutional |
| `anti_suveranist` | Anti-suveranist | 🌍 | #C62828 | Civic / investigative / corrective |


## Team

- **Team name:**
- **Topic / bubble theme:**
- **Members and agents:**
  - Póka Zsuzsa - Klaudia → Agent:personalist-salvator
  - Vasile Valentina → Agent: anti-sistem
  - Spînu Andreea-Karla → Agent: anti-suveranist
  - Grosu Roberta → Agent: conspiraționist
  - Şovan Cristian-Vasile → Agent: pro-european


## Ethics and limitations

EchoChamber is a teaching and research prototype. Its agents are simulated discursive roles, not real people or representatives of real social groups. Generated outputs may include bias, unsupported claims, or amplified conflict and must be interpreted critically.

See [`reports/ethics_checklist.md`](reports/ethics_checklist.md) for the full disclaimer and limitations.


## Known issues & limitations

    Some news websites block automatic article extraction.

    Some agents may respond too generically or repetitively.

    The debate uses simplified routing logic and is not fully conversationally stable.

    The app is a local prototype and is not deployed.

    The quality of responses depends heavily on the corpus, model provider, and dataset quality.

    Free provider models may return rate-limit errors (Gemini: 20 requests/day).

    Provider quotas may affect live demonstrations.

    The system should not be interpreted as a real measurement of public opinion.

## Troubleshooting

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'langgraph'` | `pip install langgraph` |
| `ModuleNotFoundError: No module named 'dotenv'` | `pip install python-dotenv` |
| `ModuleNotFoundError: No module named 'faiss'` | `pip install faiss-cpu` |
| `ModuleNotFoundError: No module named 'sentence_transformers'` | `pip install sentence-transformers` |
| `RateLimitError` (Gemini) | Switch to DeepSeek: `--provider deepseek` or wait 15 seconds between requests |
| `FAISS index not found` | Run `python scripts/build_vectorstore.py --agent <agent_slug>` |
| `KeyError: 'agent_slug'` | Check that agent slug exists in `assets/roles/roles.yaml` |
| `BadRequestError: response_format type unavailable` | DeepSeek doesn't support JSON schema; use Gemini for structured output or modify prompt |
| `APIStatusError: 402 Insufficient Balance` | Free tier quota exceeded; switch provider or wait for quota reset |

---

## License / usage note

This project is a research and educational prototype. Outputs should be reviewed by humans before interpretation or reuse. Do not use for political persuasion, profiling, or as a substitute for empirical social research.

The code is provided for educational purposes under the course guidelines. Unauthorized commercial use, deployment as a public service, or use in political campaigns is not permitted.

---

## Acknowledgments

- Course within the Babeș-Bolyai University - Faculty of Sociology and Social Work - Master's Degree in Complex Data Analysis – coordinated by Alexe Vlad

- Corpus collected from YouTube comments and RSS feeds (public sources, used for research purposes only)