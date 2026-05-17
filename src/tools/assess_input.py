from pydantic import BaseModel
from typing import Literal

DIMENSIONS = [
    "project_type",
    "stack",
    "data_sources",
    "constraints",
    "acceptance_criteria",
    "deliverable",
    "time_available",
]

class InputAssessment(BaseModel):
    density: Literal["rich", "sparse"]
    covered_dimensions: list[str]
    missing_dimensions: list[str]


def assess_input(text: str) -> InputAssessment:
    covered = []
    missing = []

    hints = {
        "project_type":        ["pipeline", "api", "web", "agente", "cli", "app"],
        "stack":               ["python", "java", "node", "react", "spark", "sql"],
        "data_sources":        ["base de datos", "csv", "api", "kafka", "s3", "fichero"],
        "constraints":         ["límite", "sin", "no tengo", "restricción", "rate limit"],
        "acceptance_criteria": ["done", "criterio", "acepto", "validar", "funciona cuando"],
        "deliverable":         ["entrego", "resultado", "informe", "endpoint", "script"],
        "time_available":      ["días", "horas", "semanas", "hackathon", "plazo"],
    }

    text_lower = text.lower()
    for dimension, keywords in hints.items():
        if any(kw in text_lower for kw in keywords):
            covered.append(dimension)
        else:
            missing.append(dimension)

    density = "rich" if len(covered) >= 4 else "sparse"

    return InputAssessment(
        density=density,
        covered_dimensions=covered,
        missing_dimensions=missing,
    )