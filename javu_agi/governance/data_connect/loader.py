import json, os, time, pathlib, random

CACHE = os.getenv("GOV_CACHE_DIR", "data/gov_cache")
pathlib.Path(CACHE).mkdir(parents=True, exist_ok=True)


def load_baseline(country_code="XX") -> dict:
    """Mock: ganti oleh konektor nyata (WorldBank/API statistik) bila siap. Cache ke file."""
    fp = os.path.join(CACHE, f"{country_code}.json")
    if os.path.exists(fp) and time.time() - os.path.getmtime(fp) < 86400:
        return json.load(open(fp))
    # Seed baseline minimal (dummy)—nanti konek ke API real:
    data = {"gdp": 100_000, "gini": 0.42, "unemployment": 0.11, "edu_index": 0.55}
    json.dump(data, open(fp, "w"))
    return data
