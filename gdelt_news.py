import json
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


def search_news(startup_name: str) -> list[dict[str, str]]:
    params = urlencode({
        "query": f'"{startup_name}" ("regtech" OR "compliance")',
        "mode": "ArtList",
        "format": "json",
        "maxrecords": 5,
        "timespan": "30d",
    })
    url = f"https://api.gdeltproject.org/api/v2/doc/doc?{params}"

    for attempt in range(2):
        try:
            with urlopen(url, timeout=30) as response:
                data = json.load(response)
            break
        except HTTPError as error:
            if error.code == 429 and attempt == 0:
                print("   GDELT rate limit. Retrying in 10 seconds.")
                sleep(10)
                continue
            raise RuntimeError(f"GDELT returned HTTP {error.code}.") from None
        except (URLError, TimeoutError):
            raise RuntimeError("Could not connect to GDELT or the request timed out.") from None
        except json.JSONDecodeError:
            raise RuntimeError("GDELT returned a response that was not JSON.") from None

    if not isinstance(data, dict) or not isinstance(data.get("articles"), list):
        raise RuntimeError("GDELT returned an unexpected response format.")

    return [
        {
            "title": article.get("title") or "Untitled",
            "url": article["url"],
            "seen_date": article.get("seendate") or "",
        }
        for article in data["articles"]
        if isinstance(article, dict) and article.get("url")
    ]