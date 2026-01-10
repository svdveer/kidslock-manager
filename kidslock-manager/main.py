import logging, threading, time, sqlite3, requests, subprocess, json, os, datetime
import paho.mqtt.client as mqtt
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KidsLock")
DB_PATH = "/data/kidslock.db"

# --- DB & MQTT LOGICA (Blijft gelijk aan v1.6.0) ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS tv_config (name TEXT PRIMARY KEY, ip TEXT, daily_limit INTEGER, bedtime TEXT, no_limit INTEGER DEFAULT 0, elapsed REAL DEFAULT 0)')
    conn.commit()
    conn.close()

init_db()
tv_states = {}
data_lock = threading.RLock()

# (Houd hier je MQTT configuratie en monitor loop uit v1.6.0 aan)
# ... [MQTT ON_CONNECT / ON_MESSAGE / MONITOR LOOP] ...

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    tvs_list = [{"name": n, **s} for n, s in tv_states.items()]
    return templates.TemplateResponse("index.html", {"request": request, "tvs": tvs_list})

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT name, ip, daily_limit, bedtime, no_limit FROM tv_config").fetchall()
    conn.close()
    return templates.TemplateResponse("settings.html", {"request": request, "tvs": rows})

@app.post("/api/add_tv")
async def add_tv(name: str = Form(...), ip: str = Form(...), limit: int = Form(...), bedtime: str = Form(...), no_limit: int = Form(...)):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR REPLACE INTO tv_config (name, ip, daily_limit, bedtime, no_limit) VALUES (?, ?, ?, ?, ?)",
                     (name, ip, limit, bedtime, no_limit))
    return {"status": "ok"}

@app.post("/api/delete_tv/{name}")
async def delete_tv(name: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM tv_config WHERE name = ?", (name,))
    return {"status": "ok"}

@app.post("/api/{action}/{name}")
async def api_handler(action: str, name: str, minutes: int = Form(None)):
    with data_lock:
        if name in tv_states:
            s = tv_states[name]
            if action == "toggle_lock":
                act = "unlock" if s["locked"] else "lock"
                try: requests.post(f"http://{s['ip']}:8080/{act}", timeout=2); s["locked"] = not s["locked"]
                except: pass
            elif action == "add_time":
                s["remaining"] += minutes
            elif action == "reset":
                s["remaining"] = float(s["limit"]); s["elapsed"] = 0.0
                try: requests.post(f"http://{s['ip']}:8080/unlock", timeout=2); s["locked"] = False
                except: pass
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)