import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def write_config(tmp_path, **overrides):
    cfg = {
        "api_key": "test-key",
        "daemon_port": 55991,
        "dim": 64,
        "sparsity_k": 8,
        "iters": 3,
        "min_invert": 0.925,
        "dream_probability": 0.0,
        "plugin": "soc_check",
    }
    cfg.update(overrides)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg))
    return path, cfg


def env_for(tmp_path, config_path):
    env = os.environ.copy()
    env["SEEM_CONFIG"] = str(config_path)
    env["SEEM_TWINS_DIR"] = str(tmp_path / "twins")
    env["SEEM_SIM_DELAY"] = "0"
    env["PYTHONHASHSEED"] = "0"
    return env


def run_seem(tmp_path, config_path, args):
    proc = subprocess.run(
        [PY, str(ROOT / "seem.py"), *args],
        cwd=ROOT,
        env=env_for(tmp_path, config_path),
        text=True,
        capture_output=True,
        check=False,
    )
    return proc


def last_json(stdout):
    start = stdout.rfind("{")
    assert start != -1, stdout
    return json.loads(stdout[start:])


def test_help_without_config_file():
    proc = subprocess.run(
        [PY, str(ROOT / "seem.py"), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "init" in proc.stdout
    assert "daemon" in proc.stdout


def test_init_do_persists_routes_and_gates(tmp_path):
    config_path, _cfg = write_config(tmp_path)
    init = run_seem(tmp_path, config_path, ["init", "brian_new"])
    assert init.returncode == 0, init.stderr
    first = run_seem(tmp_path, config_path, ["do", "alpha intent"])
    assert first.returncode == 0, first.stderr + first.stdout
    payload = last_json(first.stdout)
    assert payload["status"] in {"SUCCESS", "REPAIRED"}
    assert payload["twin"] == "brian_new"
    assert isinstance(payload["fidelity"], float)
    assert -1.0 <= payload["fidelity"] <= 1.0
    assert payload["route_id"]
    state_path = tmp_path / "twins" / "brian_new" / "state.json"
    state = json.loads(state_path.read_text())
    assert state["gates"] == {"alpha": False, "beta": False}
    assert payload["route_id"] in state["routes"]
    log_text = (tmp_path / "twins" / "brian_new" / "missions.log").read_text()
    assert "alpha intent" in log_text
    before = set(state["routes"])
    second = run_seem(tmp_path, config_path, ["do", "beta intent"])
    assert second.returncode == 0, second.stderr + second.stdout
    state2 = json.loads(state_path.read_text())
    assert before <= set(state2["routes"])
    status = run_seem(tmp_path, config_path, ["status"])
    assert "Active Twin: brian_new" in status.stdout
    assert "Dim: 64" in status.stdout


def test_switch_isolates_twins(tmp_path):
    config_path, _cfg = write_config(tmp_path)
    assert run_seem(tmp_path, config_path, ["init", "alice"]).returncode == 0
    assert run_seem(tmp_path, config_path, ["init", "bob"]).returncode == 0
    assert run_seem(tmp_path, config_path, ["switch", "alice"]).returncode == 0
    done = run_seem(tmp_path, config_path, ["do", "alice note"])
    assert done.returncode == 0, done.stderr + done.stdout
    alice_routes = json.loads((tmp_path / "twins" / "alice" / "state.json").read_text())["routes"]
    bob_routes = json.loads((tmp_path / "twins" / "bob" / "state.json").read_text()).get("routes", {})
    assert alice_routes
    assert bob_routes == {}
    missing = run_seem(tmp_path, config_path, ["switch", "nobody"])
    assert missing.returncode == 1


def test_missing_plugin_is_reported(tmp_path):
    config_path, _cfg = write_config(tmp_path, plugin="not_a_plugin")
    assert run_seem(tmp_path, config_path, ["init", "brian_new"]).returncode == 0
    done = run_seem(tmp_path, config_path, ["do", "hello"])
    assert done.returncode == 0, done.stderr + done.stdout
    assert last_json(done.stdout)["effect"] == "No plugin"


def test_empty_intent_errors(tmp_path):
    config_path, _cfg = write_config(tmp_path)
    done = run_seem(tmp_path, config_path, ["do", "   "])
    assert done.returncode == 1
    assert last_json(done.stdout)["status"] == "ERROR"


def test_council_simulated(tmp_path):
    config_path, _cfg = write_config(tmp_path, dim=32, sparsity_k=4, iters=2)
    proc = run_seem(tmp_path, config_path, ["council", "compare notes"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = last_json(proc.stdout)
    assert payload["consensus"].startswith("[SIMULATED")
    assert "No network call" in payload["note"]


def test_daemon_auth_and_mission(tmp_path):
    port = 55991
    config_path, cfg = write_config(tmp_path, daemon_port=port)
    proc = subprocess.Popen(
        [PY, str(ROOT / "seem.py"), "daemon"],
        cwd=ROOT,
        env=env_for(tmp_path, config_path),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        deadline = time.time() + 20
        ready = ""
        while time.time() < deadline:
            line = proc.stdout.readline()
            ready += line
            if "listening" in ready:
                break
            if proc.poll() is not None:
                break
        assert "listening" in ready, ready

        def ask(payload):
            with socket.create_connection(("127.0.0.1", port), timeout=10) as sock:
                sock.sendall(json.dumps(payload).encode())
                return json.loads(sock.recv(8192).decode())

        denied = ask({"auth_token": "nope", "intent": "x", "twin": "brian_new"})
        assert denied["status"] == "UNAUTHORIZED"
        allowed = ask({"auth_token": cfg["api_key"], "intent": "daemon note", "twin": "brian_new"})
        assert allowed["status"] in {"SUCCESS", "REPAIRED"}
        assert allowed["twin"] == "brian_new"
        state = json.loads((tmp_path / "twins" / "brian_new" / "state.json").read_text())
        assert state["routes"]
    finally:
        proc.send_signal(2)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
