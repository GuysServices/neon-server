import json
import os
import socket
import time
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get('PORT', 8000))
DB_FILE = 'leaderboard.json'
TRADE_ROOMS_FILE = 'trade_rooms.json'

# Load Leaderboard
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r') as f:
        try:
            leaderboard = json.load(f)
        except:
            leaderboard = []
else:
    leaderboard = []

# Trade Rooms State (InMemory for speed, could be persisted)
trade_rooms = {}

def save_leaderboard():
    with open(DB_FILE, 'w') as f:
        json.dump(leaderboard, f)

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
            
        elif self.path.startswith('/api/trade_room'):
            # Usage: /api/trade_room?id=RoomID
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            room_id = query.get('id', [None])[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if room_id in trade_rooms:
                self.wfile.write(json.dumps(trade_rooms[room_id]).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"error": "Room not found"}).encode('utf-8'))
        
        elif self.path.startswith('/api/find_trade'):
            # Check if anyone is inviting YOU
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            user = query.get('user', [None])[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            invites = []
            for rid, room in trade_rooms.items():
                if room['to'] == user and room['status'] == 'inviting':
                    invites.append(room)
            self.wfile.write(json.dumps(invites).encode('utf-8'))
        else:
            super().do_GET()
            
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        if self.path == '/api/update_score':
            try:
                data = json.loads(post_data.decode('utf-8'))
                user = data.get('user')
                if user:
                    found = False
                    for entry in leaderboard:
                        if entry['user'] == user:
                            entry['wave'] = max(entry['wave'], data.get('wave', 0))
                            entry['money'] = max(entry['money'], data.get('money', 0))
                            found = True
                            break
                    if not found:
                        leaderboard.append({'user': user, 'wave': data.get('wave', 0), 'money': data.get('money', 0)})
                    save_leaderboard()
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
            except:
                self.send_response(400); self.end_headers()

        elif self.path == '/api/create_trade':
            try:
                data = json.loads(post_data.decode('utf-8'))
                # { from: 'UserA', to: 'UserB' }
                room_id = f"room_{int(time.time())}_{data['from']}"
                trade_rooms[room_id] = {
                    "id": room_id,
                    "from": data['from'],
                    "to": data['to'],
                    "offer_from": [],
                    "offer_to": [],
                    "lock_from": False,
                    "lock_to": False,
                    "status": "inviting"
                }
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "room_id": room_id}).encode('utf-8'))
            except:
                self.send_response(400); self.end_headers()

        elif self.path == '/api/join_trade':
            try:
                data = json.loads(post_data.decode('utf-8'))
                room_id = data['room_id']
                if room_id in trade_rooms:
                    trade_rooms[room_id]['status'] = 'active'
                self.send_response(200); self.send_header('Access-Control-Allow-Origin', '*'); self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
            except:
                self.send_response(400); self.end_headers()

        elif self.path == '/api/sync_trade':
            try:
                data = json.loads(post_data.decode('utf-8'))
                # { room_id, user, offer, lock }
                rid = data['room_id']
                if rid in trade_rooms:
                    room = trade_rooms[rid]
                    if data['user'] == room['from']:
                        room['offer_from'] = data['offer']
                        room['lock_from'] = data['lock']
                    else:
                        room['offer_to'] = data['offer']
                        room['lock_to'] = data['lock']
                    
                    if room['lock_from'] and room['lock_to']:
                        room['status'] = 'completed'
                
                self.send_response(200); self.send_header('Access-Control-Allow-Origin', '*'); self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
            except:
                self.send_response(400); self.end_headers()

if __name__ == '__main__':
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, GameServer)
    print(f"🚀 NEON STRIKE LIVE SERVER V3.0 RUNNING ON PORT {PORT}")
    httpd.serve_forever()
