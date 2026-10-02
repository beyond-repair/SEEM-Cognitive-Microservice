import os

import torch

from core.banel import BaNEL, Route
from core.dream import ASSIGNED_MEM_FITNESS, DreamPhase
from core.resonator import ResonatorVSA
from plugins.log_to_file import execute as log_execute
from plugins.soc_check import execute as soc_execute
from skills.hybrid_cortex import HybridCortex


def test_random_hv_is_unit_complex():
    vsa = ResonatorVSA(dim=64, sparsity_k=8, iters=3)
    hv = vsa.random_hv()
    assert hv.shape == (64,)
    assert hv.dtype == torch.complex64
    norm = torch.linalg.vector_norm(hv).item()
    assert abs(norm - 1.0) < 1e-4


def test_bind_and_unbind_return_finite_score():
    vsa = ResonatorVSA(dim=64, sparsity_k=8, iters=3)
    a = vsa.random_hv()
    b = vsa.random_hv()
    composite = vsa.bind(a, b)
    recovered, score = vsa.unbind(composite, b)
    assert composite.shape == (64,)
    assert recovered.shape == (64,)
    assert isinstance(score, float)
    assert score == score  # not NaN
    assert -1.0 - 1e-5 <= score <= 1.0 + 1e-5


def test_sparsity_clamped_when_k_exceeds_dim():
    vsa = ResonatorVSA(dim=32, sparsity_k=1000, iters=2)
    assert vsa.sparsity_k == 32
    _, score = vsa.unbind(vsa.random_hv(), vsa.random_hv())
    assert -1.0 - 1e-5 <= score <= 1.0 + 1e-5


def test_dim_below_codebook_minimum_raises():
    try:
        ResonatorVSA(dim=2, sparsity_k=1, iters=1)
    except ValueError as exc:
        assert "dim" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_banel_update_and_unknown_route():
    vsa = ResonatorVSA(dim=32, sparsity_k=4, iters=2)
    banel = BaNEL(min_invert=0.925)
    banel.register_route(Route("r1", vsa.random_hv(), fitness=0.2))
    banel.update("missing", 0.99, True)
    assert "missing" not in banel.routes
    banel.update("r1", 0.4, True)
    assert banel.routes["r1"].successes == 1
    assert banel.routes["r1"].fitness == 0.4
    banel.update("r1", 0.1, False)
    assert banel.routes["r1"].successes == 1
    assert banel.routes["r1"].fitness == 0.4


def test_micro_dream_registers_child():
    vsa = ResonatorVSA(dim=32, sparsity_k=4, iters=2)
    banel = BaNEL()
    parent = Route("r1", vsa.random_hv(), fitness=0.5)
    banel.register_route(parent)
    child = banel.trigger_micro_dream("r1", vsa, vsa.random_hv())
    assert child is not None
    assert child.id.startswith("r1_dream_")
    assert child.fitness == parent.fitness * 1.05
    assert child.id in banel.routes
    assert banel.trigger_micro_dream("absent", vsa, vsa.random_hv()) is None


def test_dream_consolidate_needs_two_candidates():
    vsa = ResonatorVSA(dim=32, sparsity_k=4, iters=2)
    banel = BaNEL()
    dream = DreamPhase(banel)
    assert dream.consolidate() is None
    only = Route("s0", vsa.random_hv(), fitness=0.99)
    only.successes = 5
    banel.register_route(only)
    assert dream.consolidate() is None
    second = Route("s1", vsa.random_hv(), fitness=0.99)
    second.successes = 5
    banel.register_route(second)
    cid = dream.consolidate()
    assert cid.startswith("mem_")
    assert banel.routes[cid].fitness == ASSIGNED_MEM_FITNESS


def test_soc_check_logs_score(tmp_path):
    log_path = tmp_path / "missions.log"
    effect = soc_execute(0.123456, {"intent": "note", "twin": "t", "log_path": str(log_path)})
    text = log_path.read_text()
    assert "fidelity=0.123456" in text
    assert "intent=note" in text
    assert "logged fidelity=0.1235" in effect


def test_log_to_file_gate_and_optional_path(tmp_path):
    low = log_execute(0.5, {"intent": "x", "log_path": str(tmp_path / "out.txt")})
    assert low.startswith("FAILURE")
    assert not (tmp_path / "out.txt").exists()
    high = log_execute(0.97, {"intent": "ship", "log_path": str(tmp_path / "out.txt")})
    assert high.startswith("SUCCESS")
    assert "ship" in (tmp_path / "out.txt").read_text()


def test_hybrid_cortex_is_simulated():
    os.environ["SEEM_SIM_DELAY"] = "0"
    vsa = ResonatorVSA(dim=16, sparsity_k=4, iters=2)
    import asyncio
    result = asyncio.run(HybridCortex(vsa).execute("local note"))
    assert result["consensus"].startswith("[SIMULATED")
    assert isinstance(result["hv_checksum"], int)
