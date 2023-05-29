from http.server import SimpleHTTPRequestHandler
import socketserver

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    PORT = 8001
    Handler = CORSRequestHandler
    httpd = socketserver.TCPServer(("", PORT), Handler)
    print("Server running at http://localhost:{}".format(PORT))
    httpd.serve_forever()
