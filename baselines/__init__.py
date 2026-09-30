from baselines.fixed import FixedAgent
from baselines.adaptive import AdaptiveAgent
from baselines.search import SearchAgent
from baselines.self_evolving import SelfEvolvingAgent
from baselines.agm import AGMAgent

AGENT_TYPES = {"fixed": FixedAgent, "adaptive": AdaptiveAgent, "search": SearchAgent,
               "self_evolving": SelfEvolvingAgent, "agm": AGMAgent}


def build_agent(name, config, registry):
    kind = config.get("type", name)
    if kind not in AGENT_TYPES:
        raise ValueError(f"unknown agent type {kind!r}; known: {sorted(AGENT_TYPES)}")
    return AGENT_TYPES[kind](name, config, registry)
