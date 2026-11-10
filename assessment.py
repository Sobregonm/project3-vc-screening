def assess_geography(
    headquarters: list[dict[str, str]],
    allowed_countries: list[str],
) -> dict:
    countries = {}
    sources = []

    for item in headquarters:
        country = item.get("country", "").strip()
        source = item.get("source", "").strip()
        if country and source:
            countries[country.casefold()] = country
            sources.append(source)

    if not countries:
        return {
            "status": "Not verified",
            "reason": "No source explicitly identifies the headquarters country.",
            "sources": [],
        }

    if len(countries) > 1:
        return {
            "status": "Not verified",
            "reason": "Sources disagree about the headquarters country.",
            "sources": sources,
        }

    country_key, country = next(iter(countries.items()))
    allowed = {value.strip().casefold() for value in allowed_countries}
    meets = country_key in allowed

    reason = (
        f"{country} is on the fund's list of eligible headquarters countries."
        if meets
        else f"{country} is outside the fund's list of eligible headquarters countries."
    )

    return {
        "status": "Meets" if meets else "Does not meet",
        "reason": reason,
        "sources": sources,
    }

def assess_funding_stage(claims: list[dict[str, str]]) -> dict:
    stage_labels = {
        "pre seed": "pre-seed",
        "preseed": "pre-seed",
        "seed": "seed",
        **{f"series {letter}": f"series {letter}" for letter in "abcdefgh"},
    }
    recognized = []
    stages = set()

    for claim in claims:
        label = " ".join(claim["stage"].lower().replace("-", " ").split())
        if label in stage_labels:
            stages.add(stage_labels[label])
            recognized.append(claim)

    if not stages:
        status = "Not verified"
        reason = "No source clearly labels the latest funding round."
    elif len(stages) > 1:
        status = "Not verified"
        reason = "Sources give different funding-stage labels."
    elif stages <= {"pre-seed", "seed"}:
        status = "Meets"
        reason = "The identified funding stage is within the fund's range."
    else:
        status = "Does not meet"
        reason = "The identified funding stage is later than Seed."

    return {"status": status, "reason": reason, "claims": recognized}