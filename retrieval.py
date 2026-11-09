import argparse
import json
from pathlib import Path

THESIS_PATH = Path(__file__).resolve().parent / "knowledge" / "investment_thesis.json"


def retrieve_criterion(criterion_id: str) -> dict[str, str]:
    thesis = json.loads(THESIS_PATH.read_text(encoding="utf-8"))
    return {
        "fund": thesis["fund"],
        "criterion": criterion_id,
        "rule": thesis["criteria"][criterion_id],
        "source": f"knowledge/investment_thesis.json#criteria/{criterion_id}",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("criterion_id")
    args = parser.parse_args()

    try:
        result = retrieve_criterion(args.criterion_id)
    except KeyError:
        parser.error(f"Unknown criterion: {args.criterion_id}")

    print(json.dumps(result, indent=2, ensure_ascii=False))