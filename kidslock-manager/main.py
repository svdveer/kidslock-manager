import logging, threading, time, json, os, sqlite3, requests, subprocess
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import paho.mqtt.client as mqtt

# --- Logger & Config ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KidsLock")
DB_PATH = "/data/kidslock.db"
OPTIONS_PATH = "/data/options.json"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS tv_config 
                   (name TEXT PRIMARY KEY, ip TEXT, daily_limit INTEGER, bedtime TEXT)''')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(tv_config)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'no_limit' not in columns:
        conn.execute('ALTER TABLE tv_config ADD COLUMN no_limit INTEGER DEFAULT 0')
    conn.execute('CREATE TABLE IF NOT EXISTS tv_state (tv_name TEXT PRIMARY KEY, remaining REAL)')
    conn.commit()
    conn.close()

init_db()

# --- MQTT Setup ---
try:
    with open(OPTIONS_PATH, 'r') as f:
        options = json.load(f)
except:
    options = {}

mqtt_conf = options.get("mqtt", {})
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("MQTT Verbonden!")
        # We registreren de switches hier zodra we verbonden zijn

mqtt_client.on_connect = on_connect
if mqtt_conf.get("host"):
    if mqtt_conf.get("username"):
        mqtt_client.username_pw_set(mqtt_conf["username"], mqtt_conf.get("password"))
    try:
        mqtt_client.connect_async(mqtt_conf["host"], mqtt_conf.get("port", 1883))
        mqtt_client.loop_start()
    except:
        logger.error("MQTT kon niet starten, maar we gaan door...")

data_lock = threading.RLock()
tv_states = {}

def load_tvs_from_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, ip, daily_limit, bedtime, no_limit FROM tv_config")
    rows = cursor.fetchall()
    conn.close()
    
    with data_lock:
        current_names = [row[0] for row in rows]
        for name in list(tv_states.keys()):
            if name not in current_names:
                del tv_states[name]
        
        for name, ip, limit, bedtime, no_limit in rows:
            if name not in tv_states:
                tv_states[name] = {
                    "ip": ip, "limit": limit, "bedtime": bedtime, "no_limit": no_limit,
                    "online": False, "locked": False, "remaining": float(limit)
                }
            else:
                tv_states[name].update({"ip": ip, "limit": limit, "bedtime": bedtime, "no_limit": no_limit})

def monitor():
    logger.info("Monitor loop gestart.")
    last_tick = time.time()
    while True:
        load_tvs_from_db()
        delta = (time.time() - last_tick) / 60.0
        last_tick = time.time()
        
        with data_lock:
            for name, s in tv_states.items():
                # Bereikbaarheid check
                res = subprocess.run(['ping', '-c', '1', '-W', '1', s["ip"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                s["online"] = (res.returncode == 0)
                
                # ONBEPERKT MODUS
                if s.get("no_limit") == 1:
                    if s["locked"]:
                        try:
                            requests.post(f"http://{s['ip']}:8080/unlock", timeout=1.5)
                            s["locked"] = False
                        except: pass
                    continue
                
                # NORMALE MODUS
                if s["online"] and not s["locked"]:
                    s["remaining"] = max(0, s["remaining"] - delta)
                
                if s["remaining"] <= 0 and not s["locked"]:
                    try:
                        requests.post(f"http://{s['ip']}:8080/lock", timeout=1.5)
                        s["locked"] = True
                    except: pass
                
                # Update MQTT status voor HA
                if mqtt_conf.get("host"):
                    slug = name.lower().replace(" ", "_")
                    mqtt_client.publish(f"kidslock/{slug}/state", "ON" if s["locked"] else "OFF")

        time.sleep(30)

threading.Thread(target=monitor, daemon=True).start()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    tvs_list = []
    with data_lock:
        for name, s in tv_states.items():
            tvs_list.append({"name": name, **s})
    return templates.TemplateResponse("index.html", {"request": request, "tvs": tvs_list})

@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tv_config")
    tvs = cursor.fetchall()
    conn.close()
    return templates.TemplateResponse("settings.html", {"request": request, "tvs": tvs})

@app.post("/add_tv")
async def add_tv(name: str = Form(...), ip: str = Form(...), limit: int = Form(...), bedtime: str = Form(...), no_limit: int = Form(0)):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO tv_config VALUES (?, ?, ?, ?, ?)", (name, ip, limit, bedtime, no_limit))
    conn.commit()
    conn.close()
    return RedirectResponse(url="settings", status_code=303)

@app.post("/delete_tv/{name}")
async def delete_tv(name: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM tv_config WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="../settings", status_code=303)

@app.post("/toggle_lock/{name}")
async def toggle(name: str):
    with data_lock:
        if name in tv_states:
            action = "unlock" if tv_states[name]["locked"] else "lock"
            try:
                requests.post(f"http://{tv_states[name]['ip']}:8080/{action}", timeout=1.5)
                tv_states[name]["locked"] = not tv_states[name]["locked"]
            except: pass
    return RedirectResponse(url="", status_code=303)

@app.post("/add_time/{name}")
async def add_time(name: str, minutes: int = Form(...)):
    with data_lock:
        if name in tv_states:
            tv_states[name]["remaining"] += minutes
    return RedirectResponse(url="", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)