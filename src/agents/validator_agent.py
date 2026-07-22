"""validator_agent — modo FISCAL: veredicto final sobre el harness generado.

Contrasta contra el contrato (los 8 checks de validate_harness), no contra
opinión. Read-only: nunca modifica el harness.
"""

from pathlib import Path

from pydantic import BaseModel

from src.models.harness_spec import HarnessSpec
from src.tools.validate_harness import ValidationReport, validate_harness


class ValidatorResult(BaseModel):
    approved: bool
    report: ValidationReport
    informe: list[str]


def run_validator(harness_path: Path, spec: HarnessSpec) -> ValidatorResult:
    report = validate_harness(harness_path, spec)

    informe = [
        f"Check {r.check_id} falló en {r.file or '<sin fichero>'}: "
        f"esperaba {r.expected or '<sin expectativa>'}, encontró {r.found or '<nada>'}"
        for r in report.results
        if not r.passed
    ]

    return ValidatorResult(approved=report.passed, report=report, informe=informe)
