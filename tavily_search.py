import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ENV_PATH = Path(__file__).resolve().with_name(".env")


def search_startup(startup_name: str, website: str) -> list[dict[str, str]]:
    if not ENV_PATH.is_file():
        raise RuntimeError("Create the local .env file first.")

    key = next(
        (
            line.split("=", 1)[1].strip().strip("'\"")
            for line in ENV_PATH.read_text(encoding="utf-8").splitlines()
            if line.startswith("TAVILY_API_KEY=")
        ),
        "",
    )
    if not key:
        raise RuntimeError("TAVILY_API_KEY is missing from .env.")

    domain = urlsplit(website).hostname or website
    payload = {
        "query": f'"{startup_name}" {domain} product customers seed funding',
        "search_depth": "basic",
        "max_results": 5,
    }
    request = Request(
        "https://api.tavily.com/search",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            data = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"Tavily returned HTTP {error.code}.") from None
    except (URLError, TimeoutError):
        raise RuntimeError("Could not connect to Tavily or the request timed out.") from None
    except json.JSONDecodeError:
        raise RuntimeError("Tavily returned invalid JSON.") from None

    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise RuntimeError("Tavily returned an unexpected response format.")

    return [
        {
            "title": item.get("title") or "Untitled",
            "url": item["url"],
            "snippet": item.get("content") or "",
        }
        for item in data["results"]
        if isinstance(item, dict) and item.get("url")
    ]