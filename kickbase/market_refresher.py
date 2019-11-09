import json
from datetime import date, datetime, timezone
from typing import Dict, List

import pytz
import requests


class AnalysisError(Exception):
    pass




def get_budget(leagues: Dict, league_id: str) -> str:
    for l in leagues:
        if l["league_id"] == league_id:
            return l["lm"]["budget"]
    raise NameError(f"could not find league {league_id}")



def remove_from_market(player, league, auth_token):
    response = requests.delete(
        url="https://api.kickbase.com/leagues/{}/market/{}".format(league, player["id"]), headers={"Authorization": f"Bearer {auth_token}"})
    if response.status_code != 200:
        print("could not delete player from tm", response)
    else:
        print("player %s removed from tm successfully" %
              (player["firstName"]+" "+player["lastName"]))


def add_player_to_market(player, league, auth_token):
    url = "https://api.kickbase.com/leagues/%s/market" % league

    payload = "{\"playerId\":\"%s\",\"price\":%d}" % (
        player["id"], int(player["marketValue"] * 1.2))
    headers = {
        'Content-Type': "application/json",
        'Authorization': "Bearer {}".format(auth_token),
    }

    response = requests.request("POST", url, data=payload, headers=headers)
    if response.status_code == 200:
        print("player %s added to tm successfully" %
              (player["firstName"]+" "+player["lastName"]))


def get_new_offers(team, market, league_id, auth_token):
    response = requests.get(url="https://api.kickbase.com/competition/matches", params={
                            "matchDay": 1}, headers={"Authorization": f"Bearer {auth_token}"})

    # current match day +1 = next_match_day
    next_match_day = response.json()["cmd"] + 1

    # get next match day date
    response = requests.get(url="https://api.kickbase.com/competition/matches", params={
                            "matchDay": next_match_day}, headers={"Authorization": f"Bearer {auth_token}"})

    start_time = min(response.json()["m"], key=lambda x: x["d"])["d"]
    start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
    start_time = pytz.timezone('Europe/Berlin').localize(start_time)

    sell_time = start_time.replace(hour=start_time.hour - 2)
    # sell_time = start_time.replace(day=start_time.day - 1) # uncomment for dev reasons; allows to set custom match day

    # check if enough time is left to get some new offers
    time_to_sell = datetime.now(tz=pytz.timezone("Europe/Berlin")) <= sell_time

    market_ids = [p["id"] for p in market]
    if time_to_sell:
        for player in team:
            if player.get("offer") and player["offer"] < player["marketValue"]:
                remove_from_market(player, league_id, auth_token)
                market_ids.remove(player["id"])
    else:
        print("It is too late to get new offers!")

    for player in team:
        if player["id"] not in market_ids:
            add_player_to_market(player, league_id, auth_token)
