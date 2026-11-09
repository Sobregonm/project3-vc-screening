#from typing import TypedDict
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph
from retrieval import retrieve_criterion

class ScreeningState(TypedDict):
    startup_name: str
    website: str
    geography_criterion: NotRequired[dict[str, str]]


def collect_sources(state: ScreeningState) -> dict:
    print(f"1. Collect sources for {state['startup_name']}")
    return {}


def retrieve_criteria(state: ScreeningState) -> dict:
    print("2. Retrieve investment criteria")
    return {"geography_criterion": retrieve_criterion("geography")}


def assess_fit(state: ScreeningState) -> dict:
    criterion = state["geography_criterion"]
    print(f"3. Assess fit with criterion: {criterion['criterion']}")
    print(f"   Rule: {criterion['rule']}")
    print(f"   Source: {criterion['source']}")
    return {}


def prepare_report(state: ScreeningState) -> dict:
    print("4. Prepare the screening report")
    return {}


builder = StateGraph(ScreeningState)
builder.add_node("collect_sources", collect_sources)
builder.add_node("retrieve_criteria", retrieve_criteria)
builder.add_node("assess_fit", assess_fit)
builder.add_node("prepare_report", prepare_report)

builder.add_edge(START, "collect_sources")
builder.add_edge("collect_sources", "retrieve_criteria")
builder.add_edge("retrieve_criteria", "assess_fit")
builder.add_edge("assess_fit", "prepare_report")
builder.add_edge("prepare_report", END)

graph = builder.compile()

if __name__ == "__main__":
    graph.invoke({
        "startup_name": "Example Startup",
        "website": "https://example.com",
    })