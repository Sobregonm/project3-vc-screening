from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def read_page(url: str) -> dict[str, str]:
    request = Request(
        f"https://r.jina.ai/{url}",
        headers={"Accept": "text/plain"},
    )

    try:
        with urlopen(request, timeout=30) as response:
            content = response.read(24_000).decode("utf-8", errors="replace")
    except HTTPError as error:
        raise RuntimeError(f"Jina Reader returned HTTP {error.code}.") from None
    except (URLError, TimeoutError):
        raise RuntimeError("Could not connect to Jina Reader or the request timed out.") from None

    if not content.strip():
        raise RuntimeError("Jina Reader returned an empty page.")

    return {"url": url, "content": content}