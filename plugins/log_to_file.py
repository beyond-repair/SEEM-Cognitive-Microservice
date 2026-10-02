import datetime
import os


def execute(fidelity, mission_context=None):
    if fidelity < 0.96:
        return "FAILURE: Fidelity too low for safe execution."

    if mission_context and mission_context.get("log_path"):
        output_path = mission_context["log_path"]
    else:
        output_path = os.path.expanduser("~/seem_output.txt")
    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = (
        f"[{timestamp}] SEEM EFFECT: Action executed successfully\n"
        f"  Fidelity: {fidelity:.4f}\n"
        f"  Context: {mission_context.get('intent', 'N/A') if mission_context else 'N/A'}\n"
        "----------------------------------------\n"
    )

    with open(output_path, "a") as handle:
        handle.write(message)

    return f"SUCCESS: Logged to {output_path}"
