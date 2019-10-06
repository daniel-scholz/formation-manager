import argparse
import json
import operator
import os
from getpass import getpass
from typing import Dict, List

import requests


class LoginError(Exception):
    def __init__(self, mail, status_code):
        self.mail = mail
        self.code = status_code


class AnalysisError(Exception):
    pass


def parse_credentials() -> Dict:
    parser = argparse.ArgumentParser(description='parse login info')

    parser.add_argument("--mail", type=str,  help="mail")
    parser.add_argument("--password", type=str,  help="password")

    args = parser.parse_args().__dict__

    return args


def login(mail: str, password: str) -> str:
    login = requests.post(
        "https://kickbase.sky.de/api/v1/user/login", params={
            "email": mail,
            "password": password
        })
    if login.status_code == 200:
        return json.loads(login.text)["user"]["accessToken"]

    raise LoginError(mail, login.status_code)


def get_squad(auth_token: str, league_id: str):
    request = requests.get(
        f"https://api.kickbase.com/leagues/{league_id}/lineupex", headers={"Authorization": f"Bearer {auth_token}"})
    return json.loads(request.text)["players"]


def get_budget(leagues: Dict, league_id: str) -> str:
    for l in leagues:
        if l["league_id"] == league_id:
            return l["lm"]["budget"]
    raise NameError(f"could not find league {league_id}")


def get_leagues(auth_token: str)->List:
    leagues = requests.get(
        "https://api.kickbase.com/leagues?ext=true",
        headers={"Authorization": f"Bearer {auth_token}"})
    print(leagues)
    return leagues.json()["leagues"]


def get_market(auth_token: str, league_id: str) -> List:
    market = requests.get(
        f"https://api.kickbase.com/leagues/{league_id}/market", headers={
            "Authorization": f"Bearer {auth_token}"
        })
    return market.json()["players"]


def get_offers(auth_token: str, league_id: str, team: Dict, market: List, user_id: str) -> List:

    players = get_squad(
        auth_token=auth_token, league_id=league_id)
    # market = get_market(auth_token=auth_token,
    #                     league_id=league_id)
    # players = []
    for p in players:
        for mp in filter(lambda mp: p["id"] == mp["id"], market):
            if "offers" in mp.keys():
                p["offer"] = mp["offers"][0]["price"]
                for o in mp["offers"]:
                    if o["price"] > p["offer"]:
                        p["offer"] = o["price"]
                break

    return players


def to_csv(team):
    try:
        csv_str = f"TOTAL:, {team.value}, BUDGET:, {team.budget}\n"
        csv_str += f"NAME, POSITION, MARKET VALUE, OFFER\n"
        for p in team.players:
            csv_str += f"{p.name},{p.position},{p.market_value}, {p.highest_offer}\n"
        return csv_str
    except(NameError):
        pass


def run(mail: str, password: str) -> tuple:
    auth_token = login(mail, password)
    print(f"login successful {mail}")
    return get_leagues(auth_token), auth_token


if os.path.isfile("./auth_token"):
    # read auth token file
    with open("./auth_token", "r") as auth_f:
        auth_token = auth_f.read()
else:
    # read credentials from cli
    email = input("email: ")
    pw = getpass("password: ")
    auth_token = login(email, pw)
    with open("./auth_token", "w+") as auth_f:
        auth_f.write(auth_token)


leagues = get_leagues(auth_token)
print("Enter number for desired league:", [
      f"{i+1} : {leagues[i]['name']}" for i in range(0, len(leagues))], sep="\n")

i = int(input()) - 1
league = leagues[i]
league_id = league["id"]
user_id = requests.get("https://api.kickbase.com/user/settings",
                       headers={"Authorization": f"Bearer {auth_token}"}).json()["user"]["id"]

team = league["lm"]
# budget= team["budget"]
# points = team["points"]
# team_value = team["teamValue"]
# placement = team["placement"] -> "Platzierung"


with open(f"market_{leagues[i]['name']}.json", "w+") as f:
    market = get_market(auth_token, league_id)
    f.write(json.dumps(market, ensure_ascii=False))
# adds offers to players

team = get_offers(auth_token, league_id, team, market, user_id)
with open("squad-offers.json", "w+") as f:
    f.write(json.dumps(team, ensure_ascii=False))

# with open("leagues.json", "w+") as f:
#     f.write(json.dumps(leagues_json, ensure_ascii=False))

# with open("squad.json", "w+") as f:
#     f.write(json.dumps(get_squad(auth_token, league_id), ensure_ascii=False))
