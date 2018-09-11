import argparse
import io
import mimetypes
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import quote, unquote

from kickbase import analyser

# HTTPRequestHandler class


class Serv(BaseHTTPRequestHandler):
    # GET
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        if self.path == "/redirect" or self.path == "/table":
            self.send_response(301)
            self.send_header("Location", "/")
            self.end_headers()
            self.wfile.write(bytes("Redirect", 'utf-8'))

        else:
            try:
                """Respond to a GET request."""
                self.send_response(200)
                if self.path.endswith("otf"):
                    file_to_open = open(
                        f"web/static/{self.path[1:]}", "rb").read()
                    self.send_header(
                        "Content-Type", "application/x-font-opentype")
                    self.end_headers()

                    self.wfile.write(file_to_open)
                    return
                else:
                    file_to_open = open(
                        f"web/static/{self.path[1:]}", encoding="utf8").read()
                    mime_type, _ = mimetypes.guess_type(self.path)
                self.send_header("Content-Type", mime_type)
                self.end_headers()
            except (FileNotFoundError):
                self.send_response(404)
                self.end_headers()
                file_to_open = open(f"web/static/404.html").read()
            self.wfile.write(bytes(file_to_open, 'utf-8'))
        return

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf-8")
        params2 = post_data.split("&")
        params = {}
        for p in params2:
            if len(p.split("=")) > 1:
                if p.split("=")[1] != "":
                    params[p.split("=")[0]] = unquote(p.split("=")[1])
                else:
                    self.send_response(301)
                    self.send_header("Location", ".")
                    self.end_headers()
                    self.wfile.write(bytes("Try again", 'utf-8'))
                    return
        if self.path == "/choose":
            self.path = "/choose.html"
            mail = params["mail"]
            password = params["password"]
            file_to_open, auth_token = analyser.run(mail, password)

            json_resp = []
            for j in file_to_open:
                json_resp.append({"name": j["name"], "id": j["id"]})
            file_to_open = open("web/static/choose.html",
                                "r", encoding="utf-8").read()
            replacement = "<div>"
            for j in json_resp:
                replacement += f"<div class='league_option' id='league_{j['id']}'>{j['name']}</div>"
            replacement += "</div>"
            file_to_open = file_to_open.replace(
                "$$$CHOOSE$$$", replacement)

            file_to_open = file_to_open.replace(
                "$$$AUTH_TOKEN$$$", auth_token)
            # TODO implement redirect on one choice
            # if len(json_resp) == 1:
                # self.send_response(301)
                # self.send_header("Location", "/table")
            # else:
            self.send_response(200)
            mime_type, _ = mimetypes.guess_type(self.path)
            self.send_header("Content-Type", mime_type)
            self.end_headers()
            self.wfile.write(bytes(file_to_open, "utf8"))
        elif self.path == "/table":
            self.path = "/table.html"
            self.send_response(200)
            try:
                league_id = params["league_id"]
                auth_token = params["auth_token"]
                file_to_open = analyser.analyse(
                    auth_token=auth_token, league_id=league_id)
                json_resp = []

                csv_temp = file_to_open
                file_to_open = csv_to_html(file_to_open)
                with open(f"./web/static/{self.path}", "r") as f:
                    file_to_open = f.read().replace("$$$TABLE$$$", file_to_open)
                    file_to_open = file_to_open.replace(
                        "$$$CSV$$$", quote(csv_temp))
                file_to_open = str(file_to_open)
                mime_type, _ = mimetypes.guess_type(self.path)
                self.send_header("Content-Type", mime_type)
            except (analyser.AnalysisError):
                file_to_open = "analysis didn't work"
            except analyser.LoginError as err:
                file_to_open = f"could not login user {err.mail}, code {err.code}"
            # except:
                # file_to_open = "some mysterious error occured, which the developer did not foresee"

            self.end_headers()
            self.wfile.write(bytes(file_to_open, "utf8"))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                bytes("<h1>The site you are looking for does not exist</h1>", 'utf-8'))
        return


def csv_to_html(csv: str)-> str:
    lines = csv.split("\n")
    html = "<table>"
    for l in lines:
        items = l.split(",")
        html += "<tr>"
        for i in items:
            html += f"<td>{i}</td>"
        html += "</tr>"
    return html + "</table>"


def run():
    print('starting server...')
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", type=str, default="dev", help="dev or prod")
    args = parser.parse_args()
    if args.mode == "dev":
        ADDRESS = "localhost"
    elif args.mode == "prod":
        ADDRESS = ""
    elif args.mode == "room":
        ADDRESS = "192.168.1.48"
    # Server settings
    # Choose port 8080, for port 80, which is normally used for a http server, you need root access
    PORT_NUMBER = 80
    server_address = (ADDRESS, PORT_NUMBER)
    httpd = HTTPServer(server_address, Serv)
    print('running server...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        print("server stopped")


run()
