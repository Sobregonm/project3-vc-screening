#from typing import TypedDict
from typing import NotRequired, TypedDict
import argparse

from langgraph.graph import END, START, StateGraph
from retrieval import retrieve_criterion

from tavily_search import search_startup
from jina_reader import read_page
from gdelt_news import search_news
from report_writer import write_report

from assessment import assess_geography
from assessment import assess_funding_stage 
from headquarters_extractor import extract_company_evidence

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
    geography_assessment: NotRequired[dict]
    funding_assessment: NotRequired[dict]    


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
    print("3. Assess fit with criterion: geography")

    rule = state["geography_criterion"]["rule"]
    country_list = rule.removeprefix("The startup must be headquartered in ")
    allowed = [
        country.strip()
        for country in country_list.rstrip(".").replace(", or ", ", ").split(",")
    ]

    try:
        evidence = extract_company_evidence(
            state["startup_name"], state.get("sources", [])
        )
        claims = evidence["headquarters"]
        result = assess_geography(claims, allowed)
        result["claims"] = claims
        funding = assess_funding_stage(evidence["funding"])
        if evidence["rejected_funding_count"]:
            funding["status"] = "Not verified"
            funding["reason"] = (
                "Some funding claims could not be matched to their source text. "
                "Review the original sources before confirming the funding stage."
            )

    except RuntimeError as error:
        result = {
            "status": "Not verified",
            "reason": str(error),
            "claims": [],
        }
        funding = {"status": "Not verified", "reason": str(error), "claims": []}

    print(f"   {result['status']} | {result['reason']}")
    print(f"   Funding stage: {funding['status']} | {funding['reason']}")
    return {"geography_assessment": result, "funding_assessment": funding}


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
    parser = argparse.ArgumentParser(description="Generate a startup screening report.")
    parser.add_argument("startup_name", help="Name of the startup")
    parser.add_argument("website", help="Official website URL")
    args = parser.parse_args()

    graph.invoke({
        "startup_name": args.startup_name,
        "website": args.website,
    })