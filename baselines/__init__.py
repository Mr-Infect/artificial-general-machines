from baselines.fixed import FixedAgent
from baselines.adaptive import AdaptiveAgent
from baselines.search import SearchAgent
from baselines.self_evolving import SelfEvolvingAgent
from baselines.agm import AGMAgent
from baselines.agm_v2 import AGMv2Agent
from baselines.agm_v3 import AGMv3Agent

AGENT_TYPES = {"fixed": FixedAgent, "adaptive": AdaptiveAgent, "search": SearchAgent,
               "self_evolving": SelfEvolvingAgent, "agm": AGMAgent, "agm_v2": AGMv2Agent, "agm_v3": AGMv3Agent}


def build_agent(name, config, registry):
    kind = config.get("type", name)
    if kind not in AGENT_TYPES:
        raise ValueError(f"unknown agent type {kind!r}; known: {sorted(AGENT_TYPES)}")
    return AGENT_TYPES[kind](name, config, registry)
