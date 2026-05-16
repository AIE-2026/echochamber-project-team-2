"""
C7 — core_graph_template.py
Template pentru core/graph.py

Scop:
Transformăm logica din notebook-ul C7 într-un modul reutilizabil.
Workflow-ul final:

START → router → agent_node → router → agent_node → ... → END

Instrucțiune:
Copiați acest fișier în core/graph.py și completați TODO-urile.
"""

from typing import TypedDict
import argparse

from langgraph.graph import StateGraph, START, END

from core.agent import generate_agent_response


# Handles folosite pentru afișarea thread-ului.
# Puteți păstra aceste valori sau le puteți adapta la agenții echipei.
HANDLES = {
    "anti_sistem": "@LibertateRO99",
    "conspirationist": "@AdevarulViu",
    "pro_european": "@EuroOptimistRO",
    "anti_suveranist": "@CetateanEU",
    "personalist_salvator": "@Marian_GS_Fan",
}


class ThreadState(TypedDict):
    stimulus: str       # textul politic inițial
    messages: list      # lista mesajelor produse până acum
    active_slugs: list  # agenții care participă
    total_turns: int    # numărul total de intervenții
    current_turn: int   # câte intervenții au fost produse
    next_slug: str      # agentul ales de router
    provider: str       # gemini / deepseek
    k: int              # numărul de fragmente recuperate din FAISS


def thread_to_text(messages):
    """
    Transformă lista de mesaje într-un text citibil.
    Acest text va fi trimis agentului ca THREAD ANTERIOR.
    """
    # TODO:
    # dacă nu există mesaje, returnează un text de tip:
    # "(nu există mesaje anterioare)"
    #
    # altfel, construiește linii de forma:
    # Turn 1 — @LibertateRO99: text mesaj
    pass


def pick_next_agent(active_slugs, current_turn):
    """
    Router simplu round-robin.
    Exemplu:
    anti_sistem → conspirationist → pro_european → anti_sistem ...
    """
    # TODO:
    # returnează agentul pe baza poziției current_turn
    # hint: folosește modulo %
    pass


def router_node(state: ThreadState):
    """
    Nodul router decide cine vorbește următorul
    sau oprește conversația dacă s-a ajuns la total_turns.
    """
    # TODO:
    # dacă state["current_turn"] >= state["total_turns"]:
    #     return {"next_slug": "__end__"}
    #
    # altfel:
    #     selectează următorul agent cu pick_next_agent()
    #     return {"next_slug": next_slug}
    pass


def route_decision(state: ThreadState):
    """
    Funcția folosită de conditional edge.
    Returnează următorul nod către care merge graful.
    """
    # TODO:
    # returnează state["next_slug"]
    pass


def make_agent_node(slug):
    """
    Creează un nod pentru un agent.
    Fiecare nod:
    - citește stimulusul;
    - citește thread-ul anterior;
    - cheamă generate_agent_response();
    - adaugă mesajul nou în messages;
    - crește current_turn.
    """

    def agent_node(state: ThreadState):
        # TODO 1:
        # transformă state["messages"] în text folosind thread_to_text()
        thread_text = None

        # TODO 2:
        # ia handle-ul agentului curent din HANDLES
        my_handle = None

        # TODO 3:
        # dacă există mesaje anterioare, identifică ultimul vorbitor
        # și construiește o instrucțiune prin care agentul răspunde direct lui
        #
        # dacă nu există mesaje, agentul este primul și reacționează la stimulus
        task = None

        # TODO 4:
        # construiește agent_input cu:
        # [STIMULUS]
        # [THREAD ANTERIOR]
        # [SARCINĂ]
        agent_input = None

        # TODO 5:
        # cheamă generate_agent_response()
        result = generate_agent_response(
            agent_slug=slug,
            stimulus=agent_input,
            provider=state["provider"],
            k=state["k"]
        )

        # TODO 6:
        # construiește new_message cu:
        # agent, slug, handle, text, turn
        new_message = None

        # TODO 7:
        # returnează update-ul pentru state:
        # messages + current_turn
        pass

    return agent_node


def build_graph(active_slugs):
    """
    Construiește graful LangGraph:
    START → router → agent_node → router → ... → END
    """
    workflow = StateGraph(ThreadState)

    # TODO 1:
    # adaugă nodul router

    # TODO 2:
    # adaugă câte un nod pentru fiecare agent din active_slugs

    # TODO 3:
    # adaugă edge START → router

    # TODO 4:
    # construiește route_map:
    # fiecare slug merge către nodul lui
    # "__end__" merge către END

    # TODO 5:
    # adaugă conditional edge din router

    # TODO 6:
    # fiecare agent trebuie să revină la router

    # TODO 7:
    # compilează și returnează graful
    pass


def run_thread(
    stimulus,
    active_slugs,
    total_turns=4,
    provider="gemini",
    k=3
):
    """
    Funcția principală folosită de notebook și aplicație.

    Returnează lista finală de mesaje.
    """
    # TODO 1:
    # construiește graful cu build_graph(active_slugs)

    # TODO 2:
    # creează initial_state

    # TODO 3:
    # rulează graph.invoke(initial_state)

    # TODO 4:
    # returnează final_state["messages"]
    pass


def main():
    """
    Permite testarea din terminal:

    python -m core.graph --agents anti_sistem conspirationist pro_european --text "CCR a decis anularea alegerilor după suspiciuni privind influențe externe." --turns 4 --provider gemini
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--agents", nargs="+", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--turns", type=int, default=4)
    parser.add_argument("--provider", default="gemini")
    parser.add_argument("--k", type=int, default=3)

    args = parser.parse_args()

    messages = run_thread(
        stimulus=args.text,
        active_slugs=args.agents,
        total_turns=args.turns,
        provider=args.provider,
        k=args.k
    )

    print(thread_to_text(messages))


if __name__ == "__main__":
    main()