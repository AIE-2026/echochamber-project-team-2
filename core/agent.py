# Import libraries for environment loading, YAML roles, LLM access and retrieval
from pathlib import Path
import argparse
import os
import yaml
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from core.retriever import Retriever


# Example terminal command for testing the agent pipeline
# python -m core.agent --agent anti_sistem --text "CCR a decis anularea alegerilor după suspiciuni privind influențe externe." --provider gemini --k 5

load_dotenv()


# Define supported LLM providers and API configuration
MODELS = {
    "gemini": {
        "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        "api_key": os.getenv("GEMINI_API_KEY"),
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    },
    "deepseek": {
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "base_url": "https://api.deepseek.com/v1",
    },
}


# Load one agent role configuration from YAML
def load_role(agent_slug, roles_path="assets/roles/roles.yaml"):
    path = Path(roles_path)

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    roles = data["agents"] if "agents" in data else data

    if agent_slug not in roles:
        raise ValueError(f"Agent not found: {agent_slug}")

    return roles[agent_slug]


# Create the LLM client for the selected provider
def make_llm(provider="gemini", temperature=0.3):
    config = MODELS[provider]

    if not config["api_key"]:
        raise ValueError(f"Missing API key for provider: {provider}")

    return ChatOpenAI(
        model=config["model"],
        api_key=config["api_key"],
        base_url=config["base_url"],
        temperature=temperature,
    )


# Build the final RAG prompt using stimulus and retrieved context
def build_prompt(stimulus, rag_text):
    return f"""
[STIMULUS]
{stimulus}

[COMENTARII SIMILARE]
{rag_text}
""".strip()


# Retrieve similar comments and generate one agent response
def generate_agent_response(
    agent_slug,
    stimulus,
    provider="gemini",
    k=5,
    temperature=0.3,
    roles_path="assets/roles/roles.yaml",
):
    role = load_role(agent_slug, roles_path)

    # Initialize semantic retriever for the selected agent
    retriever = Retriever(agent_slug)

    # Retrieve top-k similar fragments from the vector store
    chunks = retriever.search(stimulus, k=k)

    # Format retrieved fragments as prompt context
    rag_text = retriever.format_for_prompt(chunks)

    # Build the final prompt for the LLM
    prompt = build_prompt(stimulus, rag_text)

    # Initialize the selected LLM provider
    llm = make_llm(provider, temperature)

    # Create LangChain message structure
    messages = [
        SystemMessage(content=role["system"]),
        HumanMessage(content=prompt),
    ]

    # Send prompt to the LLM and generate response
    response = llm.invoke(messages)

    # Return full response payload and retrieved context
    return {
        "agent_slug": agent_slug,
        "agent_name": role.get("name", agent_slug),
        "stimulus": stimulus,
        "response": response.content.strip(),
        "rag_chunks": chunks,
        "rag_text": rag_text,
        "prompt": prompt,
        "provider": provider,
        "model": MODELS[provider]["model"],
        "temperature": temperature,
        "k": k,
    }


# Terminal test interface for the agent pipeline
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--agent", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--provider", default="gemini", choices=["gemini", "deepseek"])
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--roles", default="assets/roles/roles.yaml")

    args = parser.parse_args()

    result = generate_agent_response(
        agent_slug=args.agent,
        stimulus=args.text,
        provider=args.provider,
        k=args.k,
        temperature=args.temperature,
        roles_path=args.roles,
    )

    # Print agent information and generated response
    print("\n=== AGENT ===")
    print(result["agent_name"])

    print("\n=== STIMULUS ===")
    print(result["stimulus"])

    print("\n=== CONTEXT RECUPERAT ===")
    print(result["rag_text"])

    print("\n=== RĂSPUNS ===")
    print(result["response"])


if __name__ == "__main__":
    main()