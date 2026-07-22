# Tipos de proyecto válidos
PROJECT_TYPES = ["data_pipeline", "api", "web", "agent", "cli", "other"]

# Modos del harness
HARNESS_MODES = ["EJECUTOR", "PROFESOR"]

# Complejidad del harness
HARNESS_COMPLEXITY_LEVELS = ["simple", "standard", "complex"]

# Modos por agente (fijos, no configurables por el usuario)
AGENT_MODES = {
    "leader":      "DIRECTOR",
    "planner":     "ARQUITECTO",
    "intake":      "PROFESOR",
    "analysis":    "JUEZ",
    "generator":   "ESCRIBANO",
    "implementer": "BISTURÍ",
    "reviewer":    "FISCAL",
    "integrator":  "NOTARIO",
    "watchman":    "CENTINELA",
    "tester":      "QA",
}

# Complejidad de tarea (asignada por el planner a cada tarea del backlog)
TASK_COMPLEXITY_LEVELS = ["alta", "media", "baja"]

# Tier de modelo LLM según complejidad de la tarea — el leader lanza cada
# tarea con el tier que indica su campo "complejidad" en feature_list.json
MODEL_TIER_BY_COMPLEXITY = {
    "alta":  "potente — planificar, documentar, diseñar, decisiones de arquitectura",
    "media": "intermedio — implementación estándar de código",
    "baja":  "económico — tareas mecánicas, repetitivas o de bajo riesgo",
}

# Modelos LLM recomendados por agente
LLM_RECOMMENDATIONS = {
    "intake":      {"western": "gpt-4o",          "chinese": "qwen2.5-72b"},
    "analysis":    {"western": "o3-mini",          "chinese": "deepseek-r1"},
    "planner":     {"western": "o3-mini",          "chinese": "deepseek-r1"},
    "generator":   {"western": "claude-sonnet",    "chinese": "qwen2.5-coder"},
    "implementer": {"western": "claude-sonnet",    "chinese": "deepseek-coder-v2"},
    "reviewer":    {"western": "gemini-2.5-flash", "chinese": "deepseek-r1"},
}

# Agentes mínimos por tipo de proyecto.
# El núcleo (leader, planner, implementer, reviewer, integrator, watchman) es
# fijo y está SIEMPRE — no se añaden agentes distintos de los definidos en
# AGENT_MODES. El tipo "agent" suma tester según su propia definición.
_CORE_AGENTS = [
    "leader", "planner", "implementer", "reviewer", "integrator", "watchman",
]
MIN_AGENTS_BY_TYPE = {
    "data_pipeline": _CORE_AGENTS,
    "api":           _CORE_AGENTS,
    "web":           _CORE_AGENTS,
    "agent":         _CORE_AGENTS + ["tester"],
    "cli":           _CORE_AGENTS,
    "other":         _CORE_AGENTS,
}