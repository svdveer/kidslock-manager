import logging, threading, time, sqlite3, requests, subprocess
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KidsLock")
DB_PATH = "/data/kidslock.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS tv_config (name TEXT PRIMARY KEY, ip TEXT, daily_limit INTEGER, bedtime TEXT)')
    # Migratie: kolom toevoegen als deze ontbreekt
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(tv_config)")
    if 'no_limit' not in [c[1] for c in cursor.fetchall()]:
        conn.execute('ALTER TABLE tv_config ADD COLUMN no_limit INTEGER DEFAULT 0')
    conn.execute('CREATE TABLE IF NOT EXISTS tv_state (tv_name TEXT PRIMARY KEY, remaining REAL)')
    conn.commit()
    conn.close()

init_db()
tv_states = {}
data_lock = threading.RLock()

def load_tvs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, ip, daily_limit, bedtime, no_limit FROM tv_config")
    rows = cursor.fetchall()
    conn.close()
    with data_lock:
        for name, ip, limit, bedtime, no_limit in rows:
            if name not in tv_states:
                tv_states[name] = {"ip": ip, "limit": limit, "remaining": float(limit), "online": False, "locked": False, "no_limit": no_limit}
            else:
                tv_states[name].update({"ip": ip, "limit": limit, "no_limit": no_limit})

def monitor():
    last_tick = time.time()
    while True:
        load_tvs()
        delta = (time.time() - last_tick) / 60.0
        last_tick = time.time()
        with data_lock:
            for name, s in tv_states.items():
                res = subprocess.run(['ping', '-c', '1', '-W', '1', s["ip"]], stdout=subprocess.DEVNULL)
                s["online"] = (res.returncode == 0)
                if s["no_limit"] == 1:
                    if s["locked"]:
                        requests.post(f"http://{s['ip']}:8080/unlock", timeout=1)
                        s["locked"] = False
                    continue
                if s["online"] and not s["locked"]:
                    s["remaining"] = max(0, s["remaining"] - delta)
                if s["remaining"] <= 0 and not s["locked"]:
                    requests.post(f"http://{s['ip']}:8080/lock", timeout=1)
                    s["locked"] = True
        time.sleep(30)

threading.Thread(target=monitor, daemon=True).start()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    tvs_list = [{"name": n, **s} for n, s in tv_states.items()]
    return templates.TemplateResponse("index.html", {"request": request, "tvs": tvs_list})

@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT * FROM tv_config"); tvs = cursor.fetchall(); conn.close()
    return templates.TemplateResponse("settings.html", {"request": request, "tvs": tvs})

@app.post("/add_tv")
async def add_tv(name:str=Form(...), ip:str=Form(...), limit:int=Form(...), bedtime:str=Form(...), no_limit:int=Form(0)):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO tv_config VALUES (?,?,?,?,?)", (name, ip, limit, bedtime, no_limit))
    conn.commit(); conn.close()
    return RedirectResponse(url="settings", status_code=303)

@app.post("/api/toggle_lock/{name}")
async def toggle(name: str):
    with data_lock:
        if name in tv_states:
            action = "unlock" if tv_states[name]["locked"] else "lock"
            requests.post(f"http://{tv_states[name]['ip']}:8080/{action}", timeout=1)
            tv_states[name]["locked"] = not tv_states[name]["locked"]
    return {"status": "ok"}