"""Agent roster: spec §15 baselines B0-B11 and §16 ablations."""
from archetype.baselines.memory_agents import ArchitectureMemoryAgent, NeverAdaptAgent, PrincipleMemoryAgent, TaskMemoryAgent
from archetype.baselines.oracle import LatentOracleAgent
from archetype.baselines.simple import AdaptiveAgent, AlwaysAdaptAgent, FixedAgent, ScreenSearchAgent, SearchAgent
from archetype.baselines.transfer_agents import RandomTransferAgent, SurfaceSimilarityAgent
from archetype.learner.archetype_agent import ArchetypeAgent

AGENT_TYPES = {c.kind: c for c in (FixedAgent, AdaptiveAgent, SearchAgent, ScreenSearchAgent, TaskMemoryAgent, ArchitectureMemoryAgent, PrincipleMemoryAgent,
                                   AlwaysAdaptAgent, NeverAdaptAgent, RandomTransferAgent, SurfaceSimilarityAgent, LatentOracleAgent, ArchetypeAgent)}

ABLATIONS = ["structural_memory", "contraindications", "transfer_confidence", "counterfactual", "economics", "regime_detection", "structural_analogy", "reconstruction"]

# name -> (type, config). B-numbers follow spec §15; ablations follow §16.
ROSTER = {
    "fixed": ("fixed", {}), "adaptive": ("adaptive", {}), "search": ("search", {}), "search_screen": ("search_screen", {}),
    "task_memory": ("task_memory", {}), "architecture_memory": ("architecture_memory", {}), "principle_memory": ("principle_memory", {}),
    "always_adapt": ("always_adapt", {}), "never_adapt": ("never_adapt", {}), "random_transfer": ("random_transfer", {}),
    "surface_similarity": ("surface_similarity", {}), "latent_oracle": ("latent_oracle", {}), "archetype": ("archetype", {}),
    **{f"archetype_no_{a}": ("archetype", {a: False}) for a in ABLATIONS},
}


def build_agent(name: str):
    kind, cfg = ROSTER[name]
    return AGENT_TYPES[kind](name, cfg)
