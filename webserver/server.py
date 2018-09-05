import argparse
import cgi
import io
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote

from kickbase import formatter

# HTTPRequestHandler class


class HTTPServer_RequestHandler(BaseHTTPRequestHandler):

    # GET
    def do_GET(self):
        # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Send message back to client
        with open("./webserver/static/index.html", "r") as f:
            message = f.read()
        # Write content as utf-8 data
        self.wfile.write(bytes(message, "utf8"))
        return

    def do_POST(self):
        self.send_response(200)

        self.send_header("Content-Type", "text/csv")
        self.send_header("Content-Disposition",
                         "attachment; filename=my_squad.csv")
        self.send_header('Location', '.')
        self.end_headers()

        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode(
            "utf-8")  # <--- Gets the data itself
        credentials = post_data.split("&")
        m = credentials[0].split("=")[1]
        p = credentials[1].split("=")[1]
        l = credentials[2].split("=")[1]
        m, p, l = unquote(m), unquote(p), unquote(l).replace("+", " ")

        ret_val = formatter.run(m, p, l)
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
    print(ADDRESS)
    # Server settings
    # Choose port 8080, for port 80, which is normally used for a http server, you need root access
    PORT_NUMBER = 80

    server_address = (ADDRESS, PORT_NUMBER)
    httpd = HTTPServer(server_address, HTTPServer_RequestHandler)
    print('running server...')
    httpd.serve_forever()


run()
