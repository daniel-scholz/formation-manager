import argparse
import io
import mimetypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import quote, unquote

from kickbase import analyser

# HTTPRequestHandler class


class Serv(BaseHTTPRequestHandler):
    # GET
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        if self.path == "/redirect":
            self.send_response(301)
            self.send_header("Location", "/")
            self.end_headers()
            self.wfile.write(bytes("Redirect", 'utf-8'))

        else:
            try:
                """Respond to a GET request."""
                file_to_open = open(f"web/static/{self.path[1:]}").read()
                self.send_response(200)
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
        if self.path == "/" or self.path == "/index.html":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            params2 = post_data.split("&")
            params = {}
            for p in params2:
                params[p.split("=")[0]] = unquote(p.split("=")[1])

            mail = params["mail"]
            password = params["password"]
            league = params["league"]
            league = league.replace("+", " ")
            self.send_response(200)
            try:
                file_to_open = analyser.run(mail, password, league)
                csv_temp = file_to_open
                file_to_open = csv_to_html(file_to_open)
                with open("./web/static/table.html", "r") as f:
                    file_to_open = f.read().replace("$$$TABLE$$$", file_to_open)
                    file_to_open = file_to_open.replace("$$$CSV$$$", quote(csv_temp))
                
                mime_type, _ = mimetypes.guess_type(self.path)
                self.send_header("Content-Type", mime_type)
            except (analyser.AnalysisError):
                file_to_open = "analysis didn't work"
            except analyser.LoginError as err:
                file_to_open = f"could not login user {err.mail}, code {err.code}"
            except:
                file_to_open = "some mysterious error occured, which the developer did not foresee"

            self.end_headers()
        self.wfile.write(bytes(file_to_open, "utf8"))
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
    else:
        ADDRESS = ""
    # Server settings
    # Choose port 8080, for port 80, which is normally used for a http server, you need root access
    PORT_NUMBER = 80
    server_address = (ADDRESS, PORT_NUMBER)
    httpd = HTTPServer(server_address, Serv)
    print('running server...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("server stopped")


run()
