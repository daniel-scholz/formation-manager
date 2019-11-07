from time import timezone
import pytz
from datetime import datetime, date, timezone
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


def get_leagues(auth_token: str) -> List:
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


def remove_from_market(player, league):
    response = requests.delete(
        url="https://api.kickbase.com/leagues/{}/market/{}".format(league, player["id"]), headers={"Authorization": f"Bearer {auth_token}"})
    if response.status_code != 200:
        print("could not delete player from tm", response)
    else:
        print("player %s removed from tm succesfully" %
              (player["firstName"]+" "+player["lastName"]))


def add_player_to_market(player, league):
    url = "https://api.kickbase.com/leagues/%s/market" % league

    payload = "{\"playerId\":\"%s\",\"price\":%d}" % (
        player["id"], int(player["marketValue"]*1.2))
    headers = {
        'Content-Type': "application/json",
        'Authorization': "Bearer {}".format(auth_token),
    }

    response = requests.request("POST", url, data=payload, headers=headers)
    if response.status_code == 200:
        print("player %s added to tm successfully" %
              (player["firstName"]+" "+player["lastName"]))


try:
    # read auth token file
    with open("./auth_token", "r") as auth_f:
        auth_token = auth_f.read()
    if requests.get("https://api.kickbase.com/user/settings", headers={"Authorization": f"Bearer {auth_token}"}).status_code != 200:
        print("invalid token")
        raise ConnectionError
except (FileNotFoundError, ConnectionError):

    # read credentials from cli
    email = input("email: ")
    pw = getpass("password: ")
    auth_token = login(email, pw)
    with open("./auth_token", "w+") as auth_f:
        auth_f.write(auth_token)


leagues = get_leagues(auth_token)
print("Enter number for desired league:", [
      f"{i+1} : {leagues[i]['name']}" for i in range(0, len(leagues))], sep="\n")

# i = int(input()) - 1
i = 3-1  # for dev purposes
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

team = get_offers(auth_token, league_id, team, market, user_id)
with open("your_squad_%s.json" % leagues[i]["name"], "w+") as f:
    print("Getting your squad")
    f.write(json.dumps(
        sorted(team, key=lambda x: x["position"]), ensure_ascii=False))

response = requests.get(url="https://api.kickbase.com/competition/matches", params={
                        "matchDay": 1}, headers={"Authorization": f"Bearer {auth_token}"})

cmd = response.json()["cmd"] + 1  # current match day +1

# get next match day date
response = requests.get(url="https://api.kickbase.com/competition/matches", params={
                        "matchDay": cmd}, headers={"Authorization": f"Bearer {auth_token}"})

start_time = min(response.json()["m"], key=lambda x: x["d"])["d"]
start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
start_time = pytz.timezone('Europe/Berlin').localize(start_time)

sell_time = start_time.replace(hour=start_time.hour - 2)
# sell_time = start_time.replace(day=start_time.day - 1) dev reasons
# check if enough time is left to get some new offers
time_to_sell = datetime.now(tz=pytz.timezone("Europe/Berlin")) <= sell_time

market_ids = [p["id"] for p in market]
if time_to_sell:
    for player in team:
        if player.get("offer") and player["offer"] < player["marketValue"]:
            remove_from_market(player, league_id)
            market_ids.remove(player["id"])
else:
    print("It is too late to get new offers!")

for player in team:
    if player["id"] not in market_ids:
        add_player_to_market(player, league_id)
