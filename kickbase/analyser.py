import requests
import json
import argparse
from typing import List


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


class LoginError(Exception):
    def __init__(self, mail, status_code):
        self.mail = mail
        self.code = status_code


class AnalysisError(Exception):
    pass


class Team():
    def __init__(self, players, value, budget):
        self.players = players
        self.value = value
        self.budget = budget


def parse_credentials() -> (str, str):
    parser = argparse.ArgumentParser(description='parse login info')

    parser.add_argument("m", type=str,  help="mail")
    parser.add_argument("p", type=str,  help="password")

    args = parser.parse_args()
    return args.m, args.p


def login(mail: str, password: str) -> (int):
    login = requests.post(
        "https://kickbase.sky.de/api/v1/user/login", params={
            "email": mail,
            "password": password
        })
    if login.status_code == 200:
        return json.loads(login.text)["user"]["accessToken"]

    raise LoginError(mail, login.status_code)


def get_squad(auth_token: str, id: int):
    request = requests.get(
        f"https://api.kickbase.com/leagues/{id}/lineupex", headers={"Authorization": f"Bearer {auth_token}"})
    players_json = json.loads(request.text)["players"]
    if request.status_code != 200:
        print("get_squad failed", request.status_code)
    players = []
    total_market_value = 0
    for p in players_json:
        player = Player(p)
        players.append(player)
        total_market_value += player.market_value
    return players, total_market_value


def get_budget(leagues: json, id: str) -> int:
    for l in leagues:
        if l["id"] == id:
            return l["lm"]["budget"]
    raise NameError(f"could not find league {id}")


def get_leagues(auth_token: str) -> json:
    leagues = requests.get(
        "https://api.kickbase.com/leagues?ext=true",
        headers={"Authorization": f"Bearer {auth_token}"})

    if leagues.status_code != 200:
        raise ConnectionError(
            f"could not get leagues, status code {leagues.status_code}")
    return leagues.json()["leagues"]


def get_offers(auth_token: str, id: int, players: List) -> List:
    market = requests.get(
        f"https://api.kickbase.com/leagues/{id}/market", headers={
            "Authorization": f"Bearer {auth_token}"
        })

    for mp in market.json()["players"]:
        for p in players:
            if mp["id"] == p.id and "offers" in mp:
                for o in mp["offers"]:
                    if o["price"] > p.highest_offer:
                        p.highest_offer = o["price"]
    return players


def analyse(auth_token: str, league_id: str) -> str:
    # try:
    team = Team([], 0, 0)
    # try:
    team.budget = get_budget(leagues=get_leagues(auth_token), id=league_id)
    team.players, team.value = get_squad(
        auth_token=auth_token, id=league_id)
    team.players = get_offers(auth_token=auth_token,
                              id=league_id, players=team.players)
    return to_csv(team=team)
    #     except (NameError):
    #         # print("Poop")
    #         pass
    # except (NameError, ConnectionError):
    #     pass
    # raise AnalysisError("something went wrong during analysis")


def to_csv(team: Team) -> str:
    try:

        csv_str = f"TOTAL:, {team.value}, BUDGET:, {team.budget}\n"
        csv_str += f"NAME, POSITION, MARKET VALUE, OFFER\n"
        for p in team.players:
            csv_str += f"{p.name},{p.position},{p.market_value}, {p.highest_offer}\n"
        return csv_str
    except(NameError):
        pass


def run(mail: str, password: str) -> List[str]:
    auth_token = login(mail, password)
    print(f"login successful {mail}")
    return get_leagues(auth_token), auth_token
