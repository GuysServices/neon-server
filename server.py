import json
import os
import socket
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get('PORT', 8000))
DB_FILE = 'leaderboard.json'

if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r') as f:
        try:
            leaderboard = json.load(f)
        except:
            leaderboard = []
else:
    leaderboard = []

def save_leaderboard():
    with open(DB_FILE, 'w') as f:
        json.dump(leaderboard, f)

class GameServer(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/leaderboard':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            sorted_lb = sorted(leaderboard, key=lambda x: (x.get('wave', 0), x.get('money', 0)), reverse=True)[:100]
            self.wfile.write(json.dumps(sorted_lb).encode('utf-8'))
        else:
            super().do_GET()
            
    def do_POST(self):
        if self.path == '/api/update_score':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                user = data.get('user')
                wave = data.get('wave', 0)
                money = data.get('money', 0)
                
                if user:
                    found = False
                    for entry in leaderboard:
                        if entry['user'] == user:
                            entry['wave'] = max(entry['wave'], wave)
                            entry['money'] = max(entry['money'], money)
                            found = True
                            break
                    if not found:
                        leaderboard.append({'user': user, 'wave': wave, 'money': money})
                    
                    save_leaderboard()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, GameServer)
    ip = get_local_ip()
    print("="*50)
    print("🚀 NEON GUN TYCOON SERVER IS RUNNING 🚀")
    print("="*50)
    print(f"Play on this PC:      http://localhost:{PORT}")
    print(f"Play on your iPhone:  http://{ip}:{PORT}")
    print("="*50)
    print("Waiting for players... (Leave this window open)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
