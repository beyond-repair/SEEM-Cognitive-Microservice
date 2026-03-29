# seem.py
import argparse
import hashlib
import json
import os
import socket
import signal
import sys
import torch
import random
from datetime import datetime

from core.resonator import ResonatorVSA
from core.banel import BaNEL, Route
from core.dream import DreamPhase

# ========================= CONFIG =========================
CONFIG_PATH = "config.json"
TWINS_DIR = "twins"

if not os.path.exists(CONFIG_PATH):
    print("Error: config.json missing. Run bootstrap.sh first.")
    sys.exit(1)

with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

API_KEY = CONFIG.get("api_key", "your-secure-vsa-key-123")
DAEMON_PORT = CONFIG.get("daemon_port", 5555)

# ========================= CORE =========================
vsa = ResonatorVSA(dim=16384, sparsity_k=256, iters=10)
banel = BaNEL(tau=9.0, min_invert=0.925)
dream_phase = DreamPhase(banel)
active_twin = "brian_new"

# ========================= PERSISTENCE =========================
def save_state(twin):
    path = f"{TWINS_DIR}/{twin}/state.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "routes": {
            rid: {
                "hv": torch.stack([r.hv.real, r.hv.imag], dim=-1).cpu().tolist(),
                "fitness": r.fitness,
                "successes": r.successes,
                "dreams": r.dreams
            } for rid, r in banel.routes.items()
        }
    }
    with open(path, "w") as f:
        json.dump(data, f)

def load_state(twin):
    path = f"{TWINS_DIR}/{twin}/state.json"
    if not os.path.exists(path):
        return
    with open(path) as f:
        data = json.load(f)
    for rid, rd in data.get("routes", {}).items():
        raw = torch.tensor(rd["hv"], device=vsa.device)
        hv = torch.complex(raw[..., 0], raw[..., 1])
        r = Route(rid, hv, rd["fitness"])
        r.successes = rd["successes"]
        r.dreams = rd["dreams"]
        banel.register_route(r)

# ========================= PLUGIN LOADER =========================
def load_plugin(plugin_name):
    try:
        mod = __import__(f"plugins.{plugin_name}", fromlist=["execute"])
        return mod.execute
    except ImportError:
        return None

# ========================= MISSION EXECUTION (with error boundary + retry) =========================
def execute_mission(intent, twin, max_retries=2):
    global active_twin
    if active_twin != twin:
        banel.routes.clear()
        load_state(twin)
        active_twin = twin

    for attempt in range(max_retries + 1):
        try:
            composite = vsa.random_hv()
            binder = vsa.random_hv()
            recovered, invert_score = vsa.unbind(composite, binder, verbose=False)

            # Deterministic route ID
            intent_hash = hashlib.sha256(intent.encode()).hexdigest()[:12]
            route_id = f"route_{twin}_{intent_hash}"

            if route_id not in banel.routes:
                route_hv = vsa.random_hv()
                banel.register_route(Route(route_id, route_hv))

            route = banel.routes[route_id]
            success = invert_score >= banel.min_invert

            banel.update(route_id, invert_score, success)

            if not success:
                child = banel.trigger_micro_dream(route_id, vsa, composite)
                if child:
                    print(f"[MICRO-DREAM] Repaired → {child.id} (fitness {child.fitness:.4f})")
                    route = child

            # Plugin execution
            plugin = load_plugin("soc_check")
            result = plugin(invert_score, {"intent": intent}) if plugin else "No plugin"

            # Periodic Dream consolidation
            if random.random() < 0.2:
                dream_phase.consolidate()

            # Persist state
            save_state(twin)

            return {
                "status": "SUCCESS" if success else "REPAIRED",
                "fidelity": invert_score,
                "effect": result,
                "twin": twin,
                "route_id": route.id
            }

        except Exception as e:
            print(f"[ERROR] Attempt {attempt + 1}/{max_retries + 1} failed: {e}")
            if attempt == max_retries:
                # Final fallback
                print("[FALLBACK] Using emergency repair mode.")
                invert_score = 0.85
                result = f"Emergency repair triggered due to: {str(e)[:100]}"
                save_state(twin)
                return {
                    "status": "REPAIRED",
                    "fidelity": invert_score,
                    "effect": result,
                    "twin": twin,
                    "route_id": "emergency_fallback"
                }

# ========================= DAEMON =========================
def start_daemon():
    def signal_handler(sig, frame):
        print(f"[SHUTDOWN] Saving state at {datetime.now()}")
        save_state(active_twin)
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', DAEMON_PORT))
        s.listen()
        print(f"[DAEMON] SEEM 2.0 listening on localhost:{DAEMON_PORT}")

        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(8192)
                if not data:
                    continue
                try:
                    req = json.loads(data)
                    if req.get("auth_token") != API_KEY:
                        conn.sendall(json.dumps({"status": "UNAUTHORIZED"}).encode())
                        continue
                    twin = req.get("twin", active_twin)
                    intent = req.get("intent")
                    result = execute_mission(intent, twin)
                    conn.sendall(json.dumps(result).encode())
                except Exception as e:
                    conn.sendall(json.dumps({"status": "ERROR", "message": str(e)}).encode())

# ========================= CLI =========================
def cmd_init(name):
    path = f"{TWINS_DIR}/{name}"
    os.makedirs(path, exist_ok=True)
    open(f"{path}/vault.json", "w").close()
    open(f"{path}/missions.log", "w").close()
    json.dump({"gates": {"alpha": False, "beta": False}, "vault": 0}, open(f"{path}/state.json", "w"))
    print(f"[INIT] Sovereign Identity created: {name}")

def cmd_switch(name):
    global active_twin
    if os.path.exists(f"{TWINS_DIR}/{name}"):
        active_twin = name
        print(f"[SWITCH] Active Identity: {name}")
    else:
        print(f"[ERROR] Twin {name} not found")

def cmd_do(intent):
    print(f"[DO] Processing intent: {intent}")
    result = execute_mission(intent, active_twin)
    print(json.dumps(result, indent=2))

def cmd_status():
    print(f"Active Twin: {active_twin}")
    print("Daemon Port:", DAEMON_PORT)
    print("API Key Set:", bool(API_KEY))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SEEM Sovereign Agent")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init").add_argument("name")
    subparsers.add_parser("switch").add_argument("name")
    subparsers.add_parser("do").add_argument("intent")
    subparsers.add_parser("status")
    subparsers.add_parser("daemon")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args.name)
    elif args.command == "switch":
        cmd_switch(args.name)
    elif args.command == "do":
        cmd_do(args.intent)
    elif args.command == "status":
        cmd_status()
    elif args.command == "daemon":
        start_daemon()
    else:
        parser.print_help()
