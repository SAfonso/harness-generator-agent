# Tipos de proyecto válidos
PROJECT_TYPES = ["data_pipeline", "api", "web", "agent", "cli", "other"]

# Modos del harness
HARNESS_MODES = ["EJECUTOR", "PROFESOR"]

# Complejidad del harness
HARNESS_COMPLEXITY_LEVELS = ["simple", "standard", "complex"]

# Modos por agente (fijos, no configurables por el usuario)
AGENT_MODES = {
    "leader":      "DIRECTOR",
    "intake":      "PROFESOR",
    "analysis":    "JUEZ",
    "generator":   "ESCRIBANO",
    "implementer": "BISTURÍ",
    "reviewer":    "FISCAL",
    "tester":      "QA",
}

# Modelos LLM recomendados por agente
LLM_RECOMMENDATIONS = {
    "intake":      {"western": "gpt-4o",          "chinese": "qwen2.5-72b"},
    "analysis":    {"western": "o3-mini",          "chinese": "deepseek-r1"},
    "generator":   {"western": "claude-sonnet",    "chinese": "qwen2.5-coder"},
    "implementer": {"western": "claude-sonnet",    "chinese": "deepseek-coder-v2"},
    "reviewer":    {"western": "gemini-2.5-flash", "chinese": "deepseek-r1"},
}

# Agentes mínimos por tipo de proyecto.
# El núcleo (leader, implementer, reviewer) es fijo y está SIEMPRE — no se
# añaden agentes distintos de los definidos en AGENT_MODES. El tipo "agent"
# suma tester según su propia definición.
_CORE_AGENTS = ["leader", "implementer", "reviewer"]
MIN_AGENTS_BY_TYPE = {
    "data_pipeline": _CORE_AGENTS,
    "api":           _CORE_AGENTS,
    "web":           _CORE_AGENTS,
    "agent":         _CORE_AGENTS + ["tester"],
    "cli":           _CORE_AGENTS,
    "other":         _CORE_AGENTS,
}