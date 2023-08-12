import json
import socket
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib


UDP_IP = "127.0.0.1"
UDP_PORT = 5000


class HttpHAndler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data_parse = urllib.parse.parse_qs(post_data)
        username = data_parse.get('username', [''])[0]
        message = data_parse.get('message', [''])[0]
        message_data = {"username": username, "message": message}
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.sendto(json.dumps(message_data).encode('utf-8'), (UDP_IP, UDP_PORT))
        udp_socket.close()
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content_type', 'text.html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def run(server_class=HTTPServer, handler_class=HttpHAndler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def socket_server_thread():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((UDP_IP, UDP_PORT))
    while True:
        data, _ = udp_socket.recvfrom(1024)
        message_data = json.loads(data.decode('utf-8'))
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        with open('storage/data.json', 'a') as file:
            json.dump({timestamp: message_data}, file)
            file.write('\n')


if __name__ == '__main__':
    http_thread = threading.Thread(target=run)
    http_thread.start()
    socket_server_thread()
