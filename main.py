from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import json
import os

# --- Configuration ---
options_path = "/data/options.json"
if os.path.exists(options_path):
    with open(options_path, "r") as f:
        options = json.load(f)
else:
    options = {"tvs": []}

# Global State
data_lock = threading.RLock()
tv_states = {}
for tv in options.get("tvs", []):
    tv_states[tv["name"]] = {
    logger.info(f"MQTT Message: {topic} {payload}")
    
    # Parse topic to find TV
    with data_lock:
        for tv_name, state in tv_states.items():
            slug = tv_name.lower().replace(" ", "_")
            if topic == f"kidslock/{slug}/set":
                if payload == "ON":
                    control_tv(tv_name, "lock", "Manual MQTT Lock")
                    state["manual_override"] = True
                elif payload == "OFF":
                    control_tv(tv_name, "unlock", "Manual MQTT Unlock")
                    state["manual_override"] = True

def publish_discovery(tv_name):
    slug = tv_name.lower().replace(" ", "_")
# --- Background Monitor ---
def monitor_loop():
    last_day = datetime.now().day
    last_tick = time.time()
    
    while True:
        # Calculate exact time passed to be accurate
        current_time = time.time()
        delta_minutes = (current_time - last_tick) / 60.0
        last_tick = current_time

        current_now = datetime.now()
        
        # Reset daily limits at midnight
        if current_now.day != last_day:
            logger.info("New day! Resetting timers.")
            with data_lock:
                for tv_name, state in tv_states.items():
                    state["remaining_minutes"] = state["config"]["daily_limit"]
                    state["manual_override"] = False # Reset overrides
                    update_mqtt_state(tv_name)
            last_day = current_now.day

        # Create a copy of keys to iterate safely
        with data_lock:
            tv_names = list(tv_states.keys())

        for tv_name in tv_names:
            with data_lock:
                ip = tv_states[tv_name]["config"]["ip"]
            
            # Ping outside the lock to avoid blocking the web server
            is_online = ping_tv(ip)
            
            with data_lock:
                state = tv_states[tv_name]
                state["online"] = is_online
                
                if is_online:
                    if not state["locked"]:
                        state["remaining_minutes"] = max(0, state["remaining_minutes"] - delta_minutes)
                
                # Check Bedtime
                bedtime_str = state["config"]["bedtime"]
                bedtime = datetime.strptime(bedtime_str, "%H:%M").time()
                now_time = current_now.time()
                
                is_bedtime = False
                if now_time > bedtime or now_time < datetime.strptime("04:00", "%H:%M").time():
                    is_bedtime = True
                
                time_up = state["remaining_minutes"] <= 0
                
                if not state["manual_override"]:
                    if (time_up or is_bedtime) and not state["locked"]:
                        reason = "Bedtime" if is_bedtime else "Time Limit Reached"
                        control_tv(tv_name, "lock", reason)
                    elif not time_up and not is_bedtime and state["locked"]:
                        control_tv(tv_name, "unlock", "Time Added / Morning")
                
                update_mqtt_state(tv_name)

        time.sleep(30)

# --- FastAPI / Web Interface ---
app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    
    # Prepare display data
    display_tvs = []
    with data_lock:
        for name, state in tv_states.items():
            display_tvs.append({
                "name": name,
                "online": state["online"],
                "locked": state["locked"],
                "remaining": int(state["remaining_minutes"]),
                "limit": state["config"]["daily_limit"],
                "bedtime": state["config"]["bedtime"]
            })

    return templates.TemplateResponse("index.html", {"request": request, "tvs": display_tvs, "logs": logs})

@app.post("/add_time/{tv_name}")
async def add_time(tv_name: str, minutes: int = Form(...)):
    with data_lock:
        if tv_name in tv_states:
            tv_states[tv_name]["remaining_minutes"] += minutes
            # If we add time, we might want to clear manual override to allow auto-unlock
            tv_states[tv_name]["manual_override"] = False
            
            # Force unlock immediately if it was locked due to time
            if tv_states[tv_name]["locked"]:
                 control_tv(tv_name, "unlock", f"Added {minutes} min")
            
            log_event(tv_name, "TIME_ADDED", f"Added {minutes} minutes via Dashboard")
            update_mqtt_state(tv_name)
    return RedirectResponse(url="./", status_code=303)

@app.post("/toggle_lock/{tv_name}")
async def toggle_lock(tv_name: str):
    with data_lock:
        if tv_name in tv_states:
            state = tv_states[tv_name]
            new_action = "unlock" if state["locked"] else "lock"
            control_tv(tv_name, new_action, "Dashboard Toggle")
            state["manual_override"] = True
    return RedirectResponse(url="./", status_code=303)

# --- Startup ---
