
URL = "https://api.sleeper.app/v1/players/nfl"

def main():
    r = requests.get(URL)          
    data = r.json()
    titans = [p for p in data if p["team"] == "TEN"]  # <-- also wrong: data is a dict, not a list
    print(titans)

if __name__ == "__main__":
    main()

