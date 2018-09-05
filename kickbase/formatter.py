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


def get_tm(auth_token, league_id):
    headers = {
        "Authorization": f"Bearer {auth_token}"
    }
    request = requests.get(
        f"https://api.kickbase.com/leagues/{league_id}/market", headers=headers)
    # print(request.text)
    with open("tm.json", "w+") as f:
        f.write(request.text)


def get_squad(auth_token, league_id):
    headers = {"Authorization": f"Bearer {auth_token}"}
    request = requests.get(
        f"https://api.kickbase.com/leagues/{league_id}/lineupex", headers=headers)
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


def analyse(auth_token, league_name):
    url = "https://api.kickbase.com/leagues?ext=true"
    leagues = requests.get(
        url, headers={"Authorization": f"Bearer {auth_token}"})
    # league_name = "FUSSBALLGLOTZER2"
    # league_name = "Atos kickbase "
    if leagues.status_code == 200:
        league_json = leagues.json()["leagues"]
        for l in league_json:
            if l["name"] == league_name:
                league_id = l["id"]
        budget, total_team_value_json = find_league(league_json, league_name)
    players, total_team_value = get_squad(
        auth_token=auth_token, league_id=league_id)
    if total_team_value != total_team_value_json:
        print(
            f"something went wrong {total_team_value}!= {total_team_value_json}")

    headers = {
        "Authorization": f"Bearer {auth_token}"
    }
    market = requests.get(
        f"https://api.kickbase.com/leagues/{league_id}/market", headers=headers)

    market_players = market.json()["players"]
    for mp in market_players:
        for p in players:
            if mp["id"] == p.id and mp["offers"]:
                for o in mp["offers"]:
                    if o["price"] > p.highest_offer:
                        p.highest_offer = o["price"]
                        # print("highest offer:", p.highest_offer)
    return players, total_team_value, budget


def save(path, players, total_team_value, budget):
    csv_str = f"TOTAL:, {total_team_value}, BUDGET:, {budget}\n"
    csv_str += players_to_csv(path, players)
    return csv_str


def players_to_csv(path, ps):
    csv_str = ""
    for p in ps:
        csv_str += f"{p.name},{p.position},{p.market_value}, {p.highest_offer}\n"
    return csv_str


def run(m, p, l):
    auth_token = login(m, p)
    if auth_token == -1:
        return "fail"
    players, total_team_value, budget = analyse(auth_token, l)

    return save("my_squad.csv", players, total_team_value, budget)
