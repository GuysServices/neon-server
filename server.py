import json
import os
import socket
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get('PORT', 8000))
DB_FILE = 'leaderboard.json'
TRADE_FILE = 'trades.json'

# Load Leaderboard
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r') as f:
        try:
            leaderboard = json.load(f)
        except:
            leaderboard = []
else:
    leaderboard = []

# Load Active Trades
if os.path.exists(TRADE_FILE):
    with open(TRADE_FILE, 'r') as f:
        try:
            trades = json.load(f)
        except:
            trades = []
else:
    trades = []

def save_leaderboard():
    with open(DB_FILE, 'w') as f:
        json.dump(leaderboard, f)

def save_trades():
    with open(TRADE_FILE, 'w') as f:
        json.dump(trades, f)

class GameServer(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/leaderboard':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            sorted_lb = sorted(leaderboard, key=lambda x: (x.get('wave', 0), x.get('money', 0)), reverse=True)[:100]
            self.wfile.write(json.dumps(sorted_lb).encode('utf-8'))
            
        elif self.path.startswith('/api/get_trades'):
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            user = query.get('user', [None])[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if user:
                user_trades = [t for t in trades if t['to'] == user and t['status'] == 'pending']
                self.wfile.write(json.dumps(user_trades).encode('utf-8'))
            else:
                self.wfile.write(json.dumps([]).encode('utf-8'))
        else:
            super().do_GET()
            
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        if self.path == '/api/update_score':
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
                
        elif self.path == '/api/send_trade':
            try:
                data = json.loads(post_data.decode('utf-8'))
                data['id'] = len(trades) + 1
                data['status'] = 'pending'
                trades.append(data)
                save_trades()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "id": data['id']}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

        elif self.path == '/api/complete_trade':
            try:
                data = json.loads(post_data.decode('utf-8'))
                trade_id = data.get('tradeId')
                action = data.get('action')
                for t in trades:
                    if t['id'] == trade_id:
                        t['status'] = 'accepted' if action == 'accept' else 'declined'
                        break
                save_trades()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

if __name__ == '__main__':
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, GameServer)
    print(f"🚀 NEON STRIKE SERVER V2.0 RUNNING ON PORT {PORT}")
    httpd.serve_forever()
