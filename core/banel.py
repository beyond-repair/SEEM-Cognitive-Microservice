import torch
import random

class Route:
    def __init__(self, route_id, hv, fitness=0.5):
        self.id = route_id
        self.hv = hv
        self.fitness = fitness
        self.successes = 0
        self.dreams = 0

class BaNEL:
    def __init__(self, tau=9.0, min_invert=0.925):
        self.tau = tau
        self.min_invert = min_invert
        self.routes = {}

    def register_route(self, route: Route):
        self.routes[route.id] = route

    def update(self, route_id, invert_score, success):
        if route_id not in self.routes:
            return
        route = self.routes[route_id]
        route.fitness = max(route.fitness, invert_score)
        if success:
            route.successes += 1

    def trigger_micro_dream(self, route_id, vsa, failed_composite):
        if route_id not in self.routes:
            return None
        parent = self.routes[route_id]
        child_hv = parent.hv.clone()
        failure_imprint = vsa.bind(failed_composite, parent.hv)
        strength = 0.20 + 0.15 * (1 - parent.fitness)
        child_hv = child_hv - strength * failure_imprint
        noise = torch.randn_like(child_hv) * 0.09
        child_hv = child_hv * torch.exp(1j * noise.real)
        child_hv = torch.nn.functional.normalize(child_hv, dim=0)

        cid = f"{route_id}_dream_{random.randint(1000, 9999)}"
        child = Route(cid, child_hv, fitness=parent.fitness * 1.05)
        self.register_route(child)
        return child
