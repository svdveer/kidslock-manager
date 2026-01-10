import logging
import threading
import time
import json
import os
import sqlite3
import requests
import subprocess
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import paho.mqtt.client as mqtt

# --- Initialisatie & Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KidsLock")
OPTIONS_PATH = "/data/options.json"
DB_PATH = "/data/kidslock.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS tv_state (tv_name TEXT PRIMARY KEY, remaining_minutes REAL, last_update TEXT)')
    conn.commit()
    conn.close()

init_db()

def save_state(tv_name, minutes):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT OR REPLACE INTO tv_state VALUES (?, ?, ?)", 
                     (tv_name, minutes, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Fout bij opslaan in DB: {e}")

if os.path.exists(OPTIONS_PATH):
    with open(OPTIONS_PATH, "r") as f:
        options = json.load(f)
else:
    options = {"tvs": [], "mqtt": {}}

# --- Veilig Pingen (Fix voor RCE) ---
def is_tv_online(ip):
    try:
        # We sturen 2 pings voor betrouwbaarheid
        res = subprocess.run(['ping', '-c', '2', '-W', '1', str(ip)], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0
    except:
        return False

# --- Global State ---
data_lock = threading.RLock()
tv_states = {}
first_run_done = False

for tv in options.get("tvs", []):
    tv_states[tv["name"]] = {
        "config": tv,
        "online": False,
        "locked": False,
        "remaining_minutes": float(tv.get("daily_limit", 120)),
        "manual_override": False
    }

# --- MQTT Setup ---
mqtt_conf = options.get("mqtt", {})
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("✅ MQTT Verbonden")
        for name in tv_states:
            slug = name.lower().replace(" ", "_")
            # Discovery: Switch
            client.publish(f"homeassistant/switch/kidslock_{slug}/config", json.dumps({
                "name": f"{name} Lock",
                "command_topic": f"kidslock/{slug}/set",
                "state_topic": f"kidslock/{slug}/state",
                "unique_id": f"kidslock_{slug}_switch",
                "device": {"identifiers": [f"kidslock_{slug}"], "name": name}
            }), retain=True)
            # Discovery: Sensor voor tijd
            client.publish(f"homeassistant/sensor/kidslock_{slug}_time/config", json.dumps({
                "name": f"{name} Tijd over",
                "state_topic": f"kidslock/{slug}/time",
                "unit_of_measurement": "min",
                "unique_id": f"kidslock_{slug}_time",
                "device": {"identifiers": [f"kidslock_{slug}"], "name": name},
                "icon": "mdi:timer-sand"
            }), retain=True)
            client.subscribe(f"kidslock/{slug}/set")

mqtt_client.on_connect = on_connect
if mqtt_conf.get("username"):
    mqtt_client.username_pw_set(mqtt_conf["username"], mqtt_conf.get("password"))

try:
    mqtt_client.connect(mqtt_conf.get("host", "core-mosquitto"), mqtt_conf.get("port", 1883))
    mqtt_client.loop_start()
except Exception as e:
    logger.error(f"MQTT Fout: {e}")

# --- Control & Monitor ---
def control_tv(name, action):
    state = tv_states[name]
    try:
        requests.post(f"http://{state['config']['ip']}:8080/{action}", timeout=5)
        state["locked"] = (action == "lock")
        slug = name.lower().replace(" ", "_")
        mqtt_client.publish(f"kidslock/{slug}/state", "ON" if state["locked"] else "OFF", retain=True)
    except:
        logger.error(f"Fout bij besturen TV {name}")

def monitor_loop():
    global first_run_done
    time.sleep(10)
    last_tick = time.time()
    
    while True:
        now = datetime.now()
        delta_min = (time.time() - last_tick) / 60.0
        last_tick = time.time()
        
        with data_lock:
            for name, state in tv_states.items():
                state["online"] = is_tv_online(state["config"]["ip"])
                
                # Sla alles over als Onbeperkt aan staat
                if state["config"].get("no_limit_mode", False):
                    if state["locked"] and not state["manual_override"]:
                        control_tv(name, "unlock")
                    continue

                # TIJD AFTREKKEN: Alleen bij online EN niet op slot
                if state["online"] and not state["locked"]:
                    state["remaining_minutes"] = max(0, state["remaining_minutes"] - delta_min)
                    save_state(name, state["remaining_minutes"])
                    
                    # Live update naar HA sensor
                    slug = name.lower().replace(" ", "_")
                    mqtt_client.publish(f"kidslock/{slug}/time", int(state["remaining_minutes"]), retain=True)

                # Bedtijd check
                bt_str = state["config"].get("bedtime", "21:00")
                try:
                    bt = datetime.strptime(bt_str, "%H:%M").time()
                except:
                    bt = datetime.strptime("21:00", "%H:%M").time()
                
                is_bt = (now.time() > bt or now.time() < datetime.strptime("04:00", "%H:%M").time())
                
                # Automatische acties
                if first_run_done and not state["manual_override"]:
                    if (state["remaining_minutes"] <= 0 or is_bt) and not state["locked"]:
                        control_tv(name, "lock")
                    elif state["remaining_minutes"] > 0 and not is_bt and state["locked"]:
                        control_tv(name, "unlock")
        
        first_run_done = True
        time.sleep(30)

threading.Thread(target=monitor_loop, daemon=True).start()

# --- FastAPI Web ---
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "tvs": tv_states.values()})

@app.post("/toggle_lock/{name}")
async def toggle(name: str):
    with data_lock:
        action = "unlock" if tv_states[name]["locked"] else "lock"
        control_tv(name, action)
        tv_states[name]["manual_override"] = True
    return RedirectResponse(url="./", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)