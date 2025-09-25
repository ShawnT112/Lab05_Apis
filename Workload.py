
import requests
from datetime import datetime

PLAYERS_URL = "https://api.sleeper.app/v1/players/nfl"
STATE_URL = "https://api.sleeper.app/v1/state/nfl"
TEAM = "TEN"  # Tennessee Titans


def current_season() -> int:
    """Return the current NFL season year based on UTC date."""
    today = datetime.utcnow()
    return today.year - 1 if today.month < 4 else today.year


def get_json(url: str):
    r = requests.get(url, headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()


def to_int(x):
    try:
        return int(x)
    except Exception:
        return None


def print_table(rows, headers):
    widths = [len(h) for h in headers]
    for row in rows:
        for i, c in enumerate(row):
            widths[i] = max(widths[i], len(str(c)))
    # header
    print(" | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    print("-+-".join("-" * w for w in widths))
    # rows
    for row in rows:
        print(" | ".join(str(row[i]).ljust(widths[i]) for i in range(len(headers))))


def main():
    season = current_season()

    print(f"=== Sleeper NFL State ===")
    state = get_json(STATE_URL)
    print(f"Season: {state.get('season')}, Week: {state.get('week')}")

    print("\nFetching all NFL players from Sleeper...")
    players = get_json(PLAYERS_URL)

    titans = []
    for pid, p in players.items():
        if isinstance(p, dict) and p.get("team") == TEAM:
            name = p.get("full_name") or (p.get("first_name", "") + " " + p.get("last_name", "")).strip()
            pos = p.get("position") or ""
            age = p.get("age")
            yrs = to_int(p.get("years_exp"))
            draft_year = season - yrs if yrs is not None else ""
            titans.append([name, pos, str(age or ""), str(yrs or ""), str(draft_year)])

    titans.sort(key=lambda r: (r[1], r[0]))  # sort by position then name

    print(f"\n=== Tennessee Titans Roster (Sleeper) — Season {season} ===")
    if titans:
        print_table(titans, headers=["Name", "Pos", "Age", "YrsExp", "DraftYr(est)"])
    else:
        print("No Titans found.")

if __name__ == "__main__":
    main()

