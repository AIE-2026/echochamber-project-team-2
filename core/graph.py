# core/graph.py
# ==============
# LangGraph orchestration for the agentic debate (Tab 3).
#
# HOW THE DEBATE WORKS:
#   This is NOT a fixed round-robin. After each message, a "router" LLM call
#   decides who speaks next based on the thread content. Agents address each
#   other directly by @handle, agree or disagree with previous messages.
#
#   Flow:
#     START → [router] → [agent_X] → [router] → [agent_Y] → ... → END
#
#   The router picks the next agent based on who was just challenged,
#   who hasn't spoken recently, or who has the strongest reaction to give.
#
# Students: you don't need to modify this file.



from typing import TypedDict
import argparse

from langgraph.graph import StateGraph, START, END

from core.agent import generate_agent_response


# Handles folosite pentru afișarea thread-ului.
# Puteți păstra aceste valori sau le puteți adapta la agenții echipei.
HANDLES = {
    "conspirationist": "@AdevarulViu",
    "anti_populist": "@RomaniaLucida",
    "personalist_salvator": "@Marian_GS_Fan"
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
     # dacă nu există mesaje
    if not messages:
        return "(nu există mesaje anterioare)"

    lines = []

    # construim thread-ul
    for msg in messages:
        handle = HANDLES.get(msg["slug"], msg["slug"])

        line = (
            f'Turn {msg["turn"]} — '
            f'{handle}: '
            f'{msg["text"]}'
        )

        lines.append(line)

    return "\n".join(lines)
   


def pick_next_agent(active_slugs, current_turn):
    """
    Router simplu round-robin.
    Exemplu:
    anti_sistem → conspirationist → pro_european → anti_sistem ...
    """
    index = current_turn % len(active_slugs)
    return active_slugs[index]
  
    

def router_node(state: ThreadState):
    """
    Nodul router decide cine vorbește următorul
    sau oprește conversația dacă s-a ajuns la total_turns.
    """
    
    # dacă am ajuns la numărul maxim de intervenții
    if state["current_turn"] >= state["total_turns"]:
        return {"next_slug": "__end__"}

    # alegem următorul agent
    next_slug = pick_next_agent(
        state["active_slugs"],
        state["current_turn"]
    )

    return {"next_slug": next_slug}
   

    


def route_decision(state: ThreadState):
    """
    Funcția folosită de conditional edge.
    Returnează următorul nod către care merge graful.
    """
    return state["next_slug"]



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
        thread_text = thread_to_text(state["messages"])
        my_handle = HANDLES.get(slug, slug)

        if state["messages"]:
            last_message = state["messages"][-1]
            last_handle = HANDLES.get(last_message["slug"], last_message["slug"])
            last_text = last_message["text"]

            task = f"""
Ultimul mesaj a fost scris de {last_handle} : {last_text}
Răspunde direct lui {last_handle}. Poți fi de acord sau poți contrazice, dar trebuie să continui conversația
"""
        else:
            task = """
Ești primul agent care răspunde. Reacționează la stimulusul inițial.
"""
        agent_input = f"""
[STIMULUS]
{state["stimulus"]}

[THREAD ANTERIOR]
{thread_text}

[SARCINĂ]
Scrie ca {my_handle}.
{task}

Reguli:
- scrie 2-3 propoziții;
- nu repeta mecanic ce s-a spus deja;
- menționează explicit agentul la care răspunzi dacă există mesaj anterior;
- păstrează vocea discursivă a agentului tău;
- poți contrazice, ironiza ușor sau reformula critic, dar fără insulte, atacuri personale sau limbaj agresiv;
- trebuie să existe tensiune discursivă: pune sub semnul întrebării o idee, o presupunere sau o concluzie din mesajul anterior;
- menține conflictul la nivel de idei, nu la nivel de persoană.
"""
        result = generate_agent_response(
            agent_slug=slug,
            stimulus=agent_input,
            provider=state["provider"],
            k=state["k"]
        )
        new_message = {
            "agent": result["agent_name"],
            "slug": slug,
            "handle": my_handle,
            "text": result["response"],
            "turn": state["current_turn"] + 1
        }
        return{
            "messages": state["messages"] + [new_message],
            "current_turn": state["current_turn"] + 1
        }

    return agent_node


def build_graph(active_slugs):
    """
    Construiește graful LangGraph:
    START → router → agent_node → router → ... → END
    """
    workflow = StateGraph(ThreadState)

    workflow.add_node("router", router_node)
    
    for slug in active_slugs:
        workflow.add_node(slug, make_agent_node(slug))

    workflow.add_edge(START, "router")

    route_map = {slug: slug for slug in active_slugs}
    route_map["__end__"] = END


    workflow.add_conditional_edges(
        "router",
        route_decision,
        route_map
    )

    for slug in active_slugs:
        workflow.add_edge(slug, "router")

    return workflow.compile()



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
    graph = build_graph(active_slugs)

    initial_state = {
        "stimulus": stimulus,
        "messages": [],
        "active_slugs": active_slugs,
        "total_turns": total_turns,
        "current_turn": 0,
        "next_slug": "",
        "provider": provider,
        "k": k
    }

    final_state = graph.invoke(initial_state)

    return final_state["messages"]


def main():
    print("MAIN PORNIT")
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


