
URL = "https://api.sleeper.app/v1/players/nfl"

def main():
    r = requests.get(URL)
    data = r.json()
    titans = []
    for pid, p in data.items():
        if isinstance(p, dict) and p.get("team") == "TEN":
            name = p.get("full_name") or (p.get("first_name", "") + " " + p.get("last_name", "")).strip()
            pos = p.get("position") or ""
            age = p.get("age")
            yrs = p.get("years_exp")
            titans.append([name, pos, age, yrs])
    for t in titans:
        print(t)

if __name__ == "__main__":
    main()

