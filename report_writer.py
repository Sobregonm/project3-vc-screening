from pathlib import Path
import re

from retrieval import retrieve_criterion


REPORTS_DIR = Path(__file__).resolve().parent / "reports"
CRITERIA = (
    "business_model", "sector", "geography",
    "expansion", "stage", "exclusions",
)


def write_report(state: dict) -> Path:
    name = state["startup_name"]
    website = state["website"]
    page = state.get("company_page", {})
    sources = state.get("sources", [])
    news = state.get("news", [])

    # Jina includes a header before the actual page text.
    content = page.get("content", "")
    body = content.partition("Markdown Content:")[2] or content
    paragraphs = re.split(r"\n\s*\n", body.strip())
    excerpt = next(
        (
            " ".join(paragraph.split())[:600]
            for paragraph in paragraphs
            if len(paragraph.split()) >= 15
            and not paragraph.lstrip().startswith(("#", "!", "["))
        ),
        "",
    )

    lines = [
        f"# Startup screening — {name}",
        "",
        f"**Company website:** {website}",
        "",
        "## 1. Executive summary",
        "",
        "Preliminary recommendation: Review the evidence before deciding on a first meeting.",
        "",
        "## 2. Business model and product",
        "",
    ]

    if excerpt:
        lines += [
            f"**Company's own product description** ([official website]({page['url']})):",
            "",
            f"> {excerpt}",
            "",
            "Revenue model: Not verified.",
        ]
    else:
        lines.append("Product and business model: Not verified.")

    lines += ["", "## 3. Fit with the fund's criteria", ""]
    for criterion_id in CRITERIA:
        criterion = retrieve_criterion(criterion_id)

        result = state.get("geography_assessment")
        if criterion_id == "geography" and result:
            lines.append(
                f"- **Geography — {result['status']}.** {result['reason']}"
            )
            lines.append(f"  - Fund rule: {criterion['rule']}")
            for claim in result["claims"]:
                lines.append(
                    f"  - [{claim['source']}]({claim['source']})"
                    f" — “{claim['quote']}”"
                )
            continue

        funding = state.get("funding_assessment")
        if criterion_id == "stage" and funding:
            lines.append(
                f"- **Funding stage — {funding['status']}.** {funding['reason']}"
            )
            for claim in funding["claims"]:
                lines.append(
                    f"  - [{claim['source']}]({claim['source']})"
                    f" — “{claim['quote']}”"
                )
            lines.append("  - Full stage criterion: Not verified. "
                         "Product readiness and traction still need a separate check.")
            continue

        lines += [
            f"- **{criterion_id.replace('_', ' ').title()} — Not verified.** "
            f"{criterion['rule']} ([fund rule]({criterion['source']}))",
        ]

    lines += [
        "",
        "## 4. Technology and founders",
        "",
        "Technology stack and founder information: Not verified.",
        "",
        "## 5. Competitors and recent news",
        "",
        "Competitors: Not verified.",
        "",
        "Recent news: Not verified.",
    ]
    if state.get("news_error"):
        lines.append(f"- News search error: {state['news_error']}")
    elif news:
        lines.append("- Candidate results to check:")
        lines.extend(f"  - [{item['title']}]({item['url']})" for item in news)
    else:
        lines.append("- The news query returned no results.")

    lines += [
        "",
        "## 6. Warning signs and open questions",
        "",
        "- Confirm the funding stage and headquarters with public evidence.",
        "- Check the sector, customer traction, and any exclusions before making a decision.",
        "- Review news candidates for relevance and check their publication dates.",
        "",
        "## 7. Sources",
        "",
    ]
    if page:
        lines.append(f"- [Official company website]({page['url']}) — company description.")
    lines.extend(
        f"- [{item['title']}]({item['url']}) — search result to review."
        for item in sources
    )
    if not page and not sources:
        lines.append("- No company sources were collected.")

    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "startup"
    REPORTS_DIR.mkdir(exist_ok=True)
    report_path = REPORTS_DIR / f"{slug}-screening.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path