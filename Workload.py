import sys
from datetime import datetime
import requests

STATE_URL = "https://api.sleeper.app/v1/state/nfl"
PLAYERS_URL = "https://api.sleeper.app/v1/players/nfl"
TREND_ADD_URL = "https://api.sleeper.app/v1/players/nfl/trending/add?lookback_hours=24&limit=50"
TREND_DROP_URL = "https://api.sleeper.app/v1/players/nfl/trending/drop?lookback_hours=24&limit=50"
#chat gpt was used to help me create this
def get_json(url):
    r = requests.get(url, headers={"Accept":"application/json"}, timeout=60)
    r.raise_for_status()
    return r.json()

def season_now():
    t = datetime.utcnow()
    return t.year - 1 if t.month < 4 else t.year

def to_int(x):
    try:
        return int(x)
    except:
        return None

def truncate(s, n):
    s = "" if s is None else str(s)
    return s if len(s) <= n else s[:n-1] + "…"

def print_table(rows, headers):
    w = [len(h) for h in headers]
    for r in rows:
        for i,c in enumerate(r):
            w[i] = max(w[i], len(str(c)))
    print(" | ".join(h.ljust(w[i]) for i,h in enumerate(headers)))
    print("-+-".join("-"*x for x in w))
    for r in rows:
        print(" | ".join(str(r[i]).ljust(w[i]) for i in range(len(headers))))

def pos_of(p):
    if isinstance(p.get("position"), str) and p["position"]:
        return p["position"]
    fps = p.get("fantasy_positions") or []
    return fps[0] if fps else ""

def depth_key(p, want_pos):
    dco = p.get("depth_chart_order")
    try:
        dco = int(dco) if dco is not None else 99
    except:
        dco = 99
    yrs = p.get("years_exp")
    try:
        yrs = int(yrs) if yrs is not None else -1
    except:
        yrs = -1
    primary_match = 0 if pos_of(p) == want_pos else 1
    active_rank = 0 if (p.get("status") in (None, "Active", "ACT")) else 1
    return (primary_match, dco, -yrs, active_rank, (p.get("last_name") or "ZZZ"))

def pick(players, want_pos, count):
    pool = [p for p in players if pos_of(p) == want_pos]
    pool.sort(key=lambda p: depth_key(p, want_pos))
    return pool[:count]

def build_lineup(team_players):
    used = set()
    lineup = {}
    qb = pick(team_players, "QB", 1)
    rb = pick(team_players, "RB", 2)
    wr = pick(team_players, "WR", 2)
    te = pick(team_players, "TE", 1)
    k  = pick(team_players, "K", 1)
    dst = pick(team_players, "DEF", 1) or pick(team_players, "D/ST", 1)
    lineup["QB"] = qb
    lineup["RB"] = rb
    lineup["WR"] = wr
    lineup["TE"] = te
    lineup["K"]  = k
    if dst: lineup["DEF"] = dst
    for slot in lineup.values():
        for p in slot: used.add(str(p.get("player_id")))
    flex_pool = [p for p in team_players if pos_of(p) in ("RB","WR","TE") and str(p.get("player_id")) not in used]
    flex_pool.sort(key=lambda p: depth_key(p, pos_of(p)))
    lineup["FLEX"] = flex_pool[:1]
    return lineup

def fmt_name(p):
    return p.get("full_name") or ((p.get("first_name","")+" "+p.get("last_name","")).strip()) or str(p.get("player_id"))

def print_lineup(team, lineup):
    print(f"\n=== Best Same-Team Fantasy Lineup for {team} ===")
    order = ["QB","RB","WR","TE","FLEX","K","DEF"]
    for slot in order:
        if slot not in lineup or not lineup[slot]: continue
        players = lineup[slot]
        if slot in ("RB","WR"):
            if len(players) > 0: print(f"{slot}1: {fmt_name(players[0])} ({pos_of(players[0])})")
            if len(players) > 1: print(f"{slot}2: {fmt_name(players[1])} ({pos_of(players[1])})")
        else:
            print(f"{slot}: {fmt_name(players[0])} ({pos_of(players[0])})")

def roster_for_team(players, team):
    out = []
    s_est = season_now()
    for pid,p in players.items():
        if isinstance(p, dict) and (p.get("team") or "") == team:
            name = fmt_name(p)
            pos = p.get("position") or ""
            age = p.get("age")
            yrs = to_int(p.get("years_exp"))
            draft = s_est - yrs if yrs is not None else ""
            out.append([truncate(name,28), pos, str(age or ""), str(yrs or ""), str(draft)])
    out.sort(key=lambda r:(r[1], r[0]))
    return out

def trending_with_team(players, trend_list, team):
    rows = []
    for rec in trend_list:
        pid = str(rec.get("player_id"))
        cnt = rec.get("count","")
        p = players.get(pid)
        if not isinstance(p, dict): continue
        name = fmt_name(p)
        pteam = p.get("team") or ""
        match = "YES" if pteam == team else "NO"
        rows.append([truncate(name,28), pteam, match, str(cnt)])
    rows.sort(key=lambda r:(r[2]!="YES", r[0]))
    return rows

def main():
    team = (sys.argv[1] if len(sys.argv) > 1 else "IND").upper()
    state = get_json(STATE_URL)
    season = state.get("season")
    week = state.get("week")
    print(f"Season: {season}  Week: {week}  Team Searched: {team}")

    print("\nFetching players...")
    players = get_json(PLAYERS_URL)

    roster = roster_for_team(players, team)
    print(f"\n=== {team} Roster (Sleeper) ===")
    if roster:
        print_table(roster, ["Name","Pos","Age","YrsExp","DraftYr(est)"])
    else:
        print("No players found for that team code.")

    print("\nFetching trending adds/drops (24h)...")
    adds = get_json(TREND_ADD_URL)
    drops = get_json(TREND_DROP_URL)

    add_rows = trending_with_team(players, adds, team)
    drop_rows = trending_with_team(players, drops, team)

    print(f"\n=== Trending Adds (24h) — Player Team vs. {team} ===")
    if add_rows:
        print_table(add_rows, ["Name","PlayerTeam","OnTeam?","Adds"])
    else:
        print("No data.")

    print(f"\n=== Trending Drops (24h) — Player Team vs. {team} ===")
    if drop_rows:
        print_table(drop_rows, ["Name","PlayerTeam","OnTeam?","Drops"])
    else:
        print("No data.")

    team_players = [p for p in players.values() if isinstance(p, dict) and (p.get("team") or "") == team]
    if team_players:
        lineup = build_lineup(team_players)
        print_lineup(team, lineup)

if __name__ == "__main__":
    main()


