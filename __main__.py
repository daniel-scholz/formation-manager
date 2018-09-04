import requests
import json
import argparse


class Player():
    def __init__(self, player_json):
        self.name = player_json["lastName"]
        self.market_value = player_json["marketValue"]


def parse_credentials():
    parser = argparse.ArgumentParser(description='parse login info')
    parser.add_argument("m", type=str,  help="mail")
    parser.add_argument("p", type=str,  help="password")

    args = parser.parse_args()
    print(args.m)
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
        print(f"user {m} logged in succefully")
    else:
        print("could not login", login.status_code)
        access_token = -1

    return access_token


def get_tm(a_token):
    headers = {
        "Authorization": f"Bearer {a_token}"
    }
    request = requests.get(
        "https://api.kickbase.com/leagues/620692/market", headers=headers)
    # print(request.text)
    with open("tm.json", "w+") as f:
        f.write(request.text)


def get_squad(a_token):
    headers = {"Authorization": f"Bearer {a_token}"}
    request = requests.get(
        "https://api.kickbase.com/leagues/620692/lineupex", headers=headers)
    players_json = json.loads(request.text)["players"]

    # with open("squad.json", "w+") as f:
        # f.write(json.dumps(players_json))

    players = []
    for p in players_json:
        player = Player(p)
        players.append(player)
    players_to_csv("my_squad.csv",players)


def players_to_csv(file_name,ps):
    with open(file_name, "w+",encoding="utf-8") as f:
        for p in ps:
            f.write(f"{p.name},{p.market_value}\n")


def main():
    m, p = parse_credentials()
    access_token = login(m, p)

    if access_token != -1:
        # get_tm(access_token)
        get_squad(access_token)

    else:
        print("invalid access token")


if __name__ == "__main__":
    main()
