from src.models.harness_spec import HarnessSpec
from src.config import PROJECT_TYPES


def classify_project(spec: HarnessSpec) -> str:
    """
    Confirma el tipo de proyecto a partir de HarnessSpec parcial.
    Devuelve uno de: data_pipeline | api | web | agent | cli | other
    """
    text = f"{spec.description} {' '.join(spec.stack)}".lower()

    rules = {
        "data_pipeline": ["pipeline", "spark", "databricks", "etl", "ingesta", "delta"],
        "api":           ["api", "endpoint", "rest", "fastapi", "flask", "django"],
        "web":           ["web", "frontend", "react", "vue", "html", "css"],
        "agent":         ["agente", "agent", "llm", "herramienta", "tool", "autónomo"],
        "cli":           ["cli", "terminal", "comando", "script", "bash"],
    }

    scores = {ptype: 0 for ptype in PROJECT_TYPES}

    for ptype, keywords in rules.items():
        for kw in keywords:
            if kw in text:
                scores[ptype] += 1

    best = max(scores, key=lambda k: scores[k])

    # Si ningún tipo tiene señal clara, respeta lo que dijo el usuario
    if scores[best] == 0:
        return spec.project_type

    return best


# TODO v2: reemplazar con clasificación LLM para mayor precisión