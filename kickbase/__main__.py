import argparse
import json
from getpass import getpass
from typing import Dict, List

import requests
import kickbase.market_refresher
import kickbase.make_offers


class LoginError(Exception):
    def __init__(self, mail, status_code):
        self.mail = mail
        self.code = status_code


def parse_credentials():
    parser = argparse.ArgumentParser(description='parse login info')

    parser.add_argument("--mail", type=str,  help="mail")
    parser.add_argument("--password", type=str,  help="password")

    args = parser.parse_args().__dict__

    return args


def get_leagues(auth_token: str):
    leagues = requests.get(
        "https://api.kickbase.com/leagues?ext=true",
        headers={"Authorization": f"Bearer {auth_token}"})
    print(leagues)
    return leagues.json()["leagues"]


def login(mail: str, password: str) -> str:
    login = requests.post(
        "https://kickbase.sky.de/api/v1/user/login", params={
            "email": mail,
            "password": password
        })
    if login.status_code == 200:
        return json.loads(login.text)["user"]["accessToken"]

    raise LoginError(mail, login.status_code)


def get_market(auth_token: str, league_id: str):
    market = requests.get(
        f"https://api.kickbase.com/leagues/{league_id}/market", headers={
            "Authorization": f"Bearer {auth_token}"
        })
    return market.json()["players"]


def get_offers(auth_token: str, league_id: str) -> List:

    players = get_squad(
        auth_token=auth_token, league_id=league_id)

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


def get_squad(auth_token: str, league_id: str):
    request = requests.get(
        f"https://api.kickbase.com/leagues/{league_id}/lineupex", headers={"Authorization": f"Bearer {auth_token}"})
    return json.loads(request.text)["players"]


try:
    # read auth token file
    with open("./auth_token", "r") as auth_f:
        auth_token = auth_f.read()
    if requests.get("https://api.kickbase.com/user/settings", headers={"Authorization": f"Bearer {auth_token}"}).status_code != 200:
        print("invalid token")
        raise ConnectionError
except (FileNotFoundError, ConnectionError):

    # read credentials from cli
    email = "daniel.scholz@online.de"
    # email = input("email: ")
    # pw = getpass("password: ")
    with open("pw", "rb") as f:
        import base64
        pw = base64.b64decode(f.read()).decode("utf-8")
        auth_token = login(email, pw)
    with open("./auth_token", "w+") as auth_f:
        auth_f.write(auth_token)


leagues = get_leagues(auth_token)
print("Enter number for desired league:", [
      f"{i+1} : {leagues[i]['name']}" for i in range(0, len(leagues))], sep="\n")

# i = int(input()) - 1
i = 1 - 1  # for dev purposes

league = leagues[i]
league_id = league["id"]
user_id = requests.get("https://api.kickbase.com/user/settings",
                       headers={"Authorization": f"Bearer {auth_token}"}).json()["user"]["id"]

team = league["lm"]


market = get_market(auth_token, league_id)
with open(f"market_{leagues[i]['name']}.json", "w+") as f:
    print("Getting current transfer market")
    f.write(json.dumps(market, ensure_ascii=False))
# adds offers to players

team = get_offers(auth_token, league_id)
with open("your_squad_%s.json" % leagues[i]["name"], "w+") as f:
    print("Getting your squad")
    f.write(json.dumps(
        sorted(team, key=lambda x: x["position"]), ensure_ascii=False))

# kickbase.market_refresher.get_new_offers(team, market, league_id, auth_token)
kickbase.make_offers.offer_all()
