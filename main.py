#from typing import TypedDict
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph
from retrieval import retrieve_criterion

from tavily_search import search_startup
from jina_reader import read_page
from gdelt_news import search_news
from report_writer import write_report

class ScreeningState(TypedDict):
    startup_name: str
    website: str
    geography_criterion: NotRequired[dict[str, str]]
    sources: NotRequired[list[dict[str, str]]]
    research_error: NotRequired[str]
    company_page: NotRequired[dict[str, str]]
    page_read_error: NotRequired[str]
    news: NotRequired[list[dict[str, str]]]
    news_error: NotRequired[str]
    report_path: NotRequired[str]    


def collect_sources(state: ScreeningState) -> dict:
    print(f"1. Collect sources for {state['startup_name']}")
    updates = {"sources": [], "news": []}

    try:
        sources = search_startup(state["startup_name"], state["website"])
        updates["sources"] = sources
        print(f"   Tavily found {len(sources)} source(s).")
    except RuntimeError as error:
        updates["research_error"] = str(error)
        print(f"   Search failed: {error}")

    try:
        page = read_page(state["website"])
        updates["company_page"] = page
        print(f"   Jina read {len(page['content'])} characters from {page['url']}")
    except RuntimeError as error:
        updates["page_read_error"] = str(error)
        print(f"   Page read failed: {error}")

    try:
        news = search_news(state["startup_name"])
        updates["news"] = news
        print(f"   GDELT found {len(news)} article(s).")
        for article in news:
            print(f"   - {article['title']} | {article['url']}")
    except RuntimeError as error:
        updates["news_error"] = str(error)
        print(f"   News search failed: {error}")

    return updates

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
    report_path = write_report(state)
    print(f"   Report saved to {report_path}")
    return {"report_path": str(report_path)}


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
        "startup_name": "Kalipso",
        "website": "https://kalipso.ai/",
    })