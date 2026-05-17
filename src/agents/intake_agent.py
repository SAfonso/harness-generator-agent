"""intake_agent — non-interactive analysis of the user's raw input."""

from src.config import LLM_RECOMMENDATIONS, PROJECT_TYPES  # noqa: F401
from src.models.harness_spec import HarnessSpec, IntakeResult, LLMConfig
from src.tools.assess_input import DIMENSIONS, assess_input  # noqa: F401

_STACK_TOKENS = [
    "spark", "python", "databricks", "fastapi", "react",
    "node", "django", "flask", "kafka", "s3",
]
_DATA_SOURCE_TOKENS = ["s3", "kafka", "csv", "base de datos", "api", "fichero"]
_CONSTRAINT_TOKENS = ["sin", "límite", "restricción", "rate limit", "no tengo"]
_DELIVERABLE_TOKENS = ["script", "informe", "endpoint", "api", "web", "cli"]
_TIME_TOKENS = ["días", "horas", "semanas", "hackathon"]

_PROJECT_TYPE_HINTS = {
    "data_pipeline": ["pipeline", "etl", "ingesta", "spark", "databricks"],
    "api":           ["api", "endpoint", "rest", "fastapi", "flask", "django"],
    "web":           ["web", "frontend", "react", "vue"],
    "agent":         ["agente", "agent", "llm"],
    "cli":           ["cli", "terminal", "comando", "bash"],
}


def _present(tokens: list[str], text: str) -> list[str]:
    return [t for t in tokens if t in text]


def _detect_project_type(text: str) -> str:
    scores = {ptype: 0 for ptype in PROJECT_TYPES}
    for ptype, hints in _PROJECT_TYPE_HINTS.items():
        for hint in hints:
            if hint in text:
                scores[ptype] += 1
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "other"


def _detect_acceptance_criteria(text: str) -> list[str]:
    criteria: list[str] = []
    for marker in ("done cuando", "criterio"):
        idx = text.find(marker)
        if idx < 0:
            continue
        start = idx + len(marker)
        end = text.find(".", start)
        phrase = text[start: end if end >= 0 else None].strip(" :,;-")
        if phrase:
            criteria.append(phrase)
    return criteria


def _detect_llm_config(text: str) -> LLMConfig:
    if "recommended" in text:
        return LLMConfig(strategy="recommended")
    if "custom" in text:
        return LLMConfig(strategy="custom")
    return LLMConfig(strategy="same", default_model="gpt-4o")


def run_intake(text: str, mode: str) -> IntakeResult:
    assessment = assess_input(text)

    if assessment.density == "rich" and not assessment.missing_dimensions:
        text_lower = text.lower()
        spec = HarnessSpec(
            project_type=_detect_project_type(text_lower),
            description=text,
            stack=_present(_STACK_TOKENS, text_lower),
            data_sources=_present(_DATA_SOURCE_TOKENS, text_lower),
            constraints=_present(_CONSTRAINT_TOKENS, text_lower),
            acceptance_criteria=_detect_acceptance_criteria(text_lower),
            deliverable=", ".join(_present(_DELIVERABLE_TOKENS, text_lower)),
            time_available=", ".join(_present(_TIME_TOKENS, text_lower)),
            mode=mode,
            llm_config=_detect_llm_config(text_lower),
        )
        return IntakeResult(status="complete", spec=spec, questions=[])

    return IntakeResult(
        status="needs_input",
        spec=None,
        questions=list(assessment.missing_dimensions),
    )
