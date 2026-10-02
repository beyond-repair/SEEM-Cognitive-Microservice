"""Default mission plugin.

Records the resonator score next to the intent. It does not decide that a
security control passed, and it does not invent a fidelity threshold.
"""
import datetime
import os


def execute(fidelity, mission_context=None):
    ctx = mission_context or {}
    twin = ctx.get("twin", "unknown")
    intent = ctx.get("intent", "N/A")
    log_path = ctx.get("log_path") or os.path.join("twins", str(twin), "missions.log")
    parent = os.path.dirname(log_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    line = f"{timestamp} twin={twin} fidelity={float(fidelity):.6f} intent={intent}\n"
    with open(log_path, "a") as handle:
        handle.write(line)
    return f"logged fidelity={float(fidelity):.4f} to {log_path}"
