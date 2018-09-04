import requests
import json
import argparse


class Player():
    def __init__(self, player_json):
        self.id = player_json["id"]
        self.name = player_json["lastName"]
        self.market_value = player_json["marketValue"]
        self.highest_offer = 0
        self.average_points = player_json["averagePoints"]
        self.total_points = player_json["totalPoints"]
        self.position = player_json["position"]
        self.teamId = player_json["teamId"]
        self.for_sale = False


def parse_credentials():
    parser = argparse.ArgumentParser(description='parse login info')

    parser.add_argument("m", type=str,  help="mail")
    parser.add_argument("p", type=str,  help="password")

    args = parser.parse_args()
    return args.m, args.p


def login(m, p):
    params = {
        "email": m,
        "password": p
    }
    login = requests.post(
        "https://kickbase.sky.de/api/v1/user/login", params=params)
    if login.status_code == 200:
        access_token = json.loads(login.text)["user"]["accessToken"]
        print(
            f"user '{m}' logged in successfully\npassword 'short-penis_7cm' is correct")
    else:
        print("could not login", login.status_code)
        access_token = -1

    return access_token


def get_tm(auth_token):
    headers = {
        "Authorization": f"Bearer {auth_token}"
    }
    request = requests.get(
        "https://api.kickbase.com/leagues/620692/market", headers=headers)
    # print(request.text)
    with open("tm.json", "w+") as f:
        f.write(request.text)


def get_squad(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    request = requests.get(
        "https://api.kickbase.com/leagues/620692/lineupex", headers=headers)
    players_json = json.loads(request.text)["players"]

    # with open("squad.json", "w+") as f:
    # f.write(json.dumps(players_json))

    players = []
    total_market_value = 0
    for p in players_json:
        player = Player(p)
        players.append(player)
        total_market_value += player.market_value
    return players, total_market_value


def find_league(leagues, league_name):
    for l in leagues:
        if l["name"] == league_name:
            budget = l["lm"]["budget"]
            total_team_value_json = l["lm"]["teamValue"]
            return budget, total_team_value_json
    return 0, 0


def analyse(auth_token):
    file_name = "my_squad.csv"

    url = "https://api.kickbase.com/leagues?ext=true"
    leagues = requests.get(
        url, headers={"Authorization": f"Bearer {auth_token}"})
    league_name = "FUSSBALLGLOTZER2"
    # league_name = "Atos kickbase "

    if leagues.status_code == 200:
        league_json = leagues.json()["leagues"]
        budget, total_team_value_json = find_league(league_json, league_name)
    players, total_team_value = get_squad(auth_token=auth_token)
    if total_team_value != total_team_value_json:
        print(
            f"something went wrong {total_team_value}!= {total_team_value_json}")

    headers = {
        "Authorization": f"Bearer {auth_token}"
    }
    market = requests.get(
        "https://api.kickbase.com/leagues/620692/market", headers=headers)

    market_players = market.json()["players"]
    for mp in market_players:
        for p in players:
            if mp["id"] == p.id and mp["offers"]:
                for o in mp["offers"]:
                    if o["price"] > p.highest_offer:
                        p.highest_offer = o["price"]
                        print("highest offer:", p.highest_offer)

    file_name = "my_squad.csv"
    with open(file_name, "w+", encoding="utf-8") as f:
        f.write(f"TOTAL:, {total_team_value}, BUDGET:, {budget}\n")

    players_to_csv(file_name, players)


def players_to_csv(file_name, ps):
    with open(file_name, "a", encoding="utf-8") as f:
        for p in ps:
            f.write(
                f"{p.name},{p.position},{p.market_value}, {p.highest_offer}\n")


def main():
    m, p = parse_credentials()
    access_token = login(m, p)

    if access_token != -1:
        # get_tm(access_token)
        analyse(access_token)

    else:
        print("invalid access token")


if __name__ == "__main__":
    main()
