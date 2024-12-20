from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

from pymongo import MongoClient


import urllib.parse
import pathlib
import mimetypes
import threading
import socket



IP = "0.0.0.0"
SOCKET_PORT = 5000
HTTP_PORT = 3000
MONGO_URL = "mongodb://mongodb:27017/mydatabase"



class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("front-init/index.html")
        elif pr_url.path == "/message":
            self.send_html_file("front-init/message.html")
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("front-init/error.html", 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        self.send_data_to_socket_server(data)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_data_to_socket_server(self, data):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect((IP, SOCKET_PORT))
            sock.sendall(data)


def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", HTTP_PORT)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def run_socket_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    try:
        while True:
            data, address = sock.recvfrom(1024)
            print(f"Received data: {data.decode()} from: {address}")
            data_parse = urllib.parse.unquote_plus(data.decode())
            data_dict = {
                key: value
                for key, value in [el.split("=") for el in data_parse.split("&")]
            }
            data_dict["date"] = datetime.now().isoformat()
            
            db = get_database()
            try:
                result = db.data.insert_one(data_dict)
                print("Data successfully saved to MongoDB.")
            except Exception as e:
                print(f"Error saving data to MongoDB: {e}")
            
    except KeyboardInterrupt:
        print(f"Destroy server")
    finally:
        sock.close()


def get_database():
    client = MongoClient(MONGO_URL)
    db = client.mydatabase
    return db


if __name__ == "__main__":
    http_thread = threading.Thread(target=run_http_server)
    http_thread.start()

    socket_thread = threading.Thread(
        target=run_socket_server, args=(IP, SOCKET_PORT)
    )
    socket_thread.start()
