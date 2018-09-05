from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi
from urllib.parse import unquote
import io
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
        self.end_headers()

        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode(
            "utf-8")  # <--- Gets the data itself
        credentials = post_data.split("&")
        m = credentials[0].split("=")[1]
        p = credentials[1].split("=")[1]
        m, p = unquote(m), unquote(p)
        ret_val = formatter.run(m, p)
        self.wfile.write(bytes(ret_val, "utf8"))
        return


def run():
    print('starting server...')

    # Server settings
    # Choose port 8080, for port 80, which is normally used for a http server, you need root access
    PORT_NUMBER = 80
    server_address = ('127.0.0.1', PORT_NUMBER)
    httpd = HTTPServer(server_address, HTTPServer_RequestHandler)
    print('running server...')
    httpd.serve_forever()


run()
