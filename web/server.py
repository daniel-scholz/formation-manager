import argparse
import cgi
import io
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote

from kickbase import analyser

# HTTPRequestHandler class


class Serv(BaseHTTPRequestHandler):

    # GET
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        try:
            file_to_open = open(f"./web/static/{self.path[1:]}").read()
            self.send_response(200)
        except:
            file_to_open = "File not found"
            self.send_response(404)
        self.end_headers()
        self.wfile.write(bytes(file_to_open, 'utf-8'))
        return

    def do_POST(self):

        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode(
            "utf-8")  # <--- Gets the data itself
        credentials = post_data.split("&")
        mail = credentials[0].split("=")[1]
        password = credentials[1].split("=")[1]
        league = credentials[2].split("=")[1]
        mail, password, league = unquote(mail), unquote(password), unquote(league).replace("+", " ")
        self.send_response(200)
        try:
            ret_val = analyser.run(mail, password, league)
            # self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition",
                             "attachment; filename=my_squad.csv")
        except (analyser.AnalysisError):
            self.send_header("Content-Type", "text/html")
            ret_val = "analysis didn't work"
        except analyser.LoginError as err:
            ret_val = f"could not login user {err.mail}, code {err.code}"
        except:
            ret_val = "some mysterious error occured, which the developer did not foresee"

        self.end_headers()
        self.wfile.write(bytes(ret_val, "utf8"))
        return


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
    httpd.serve_forever()


run()
