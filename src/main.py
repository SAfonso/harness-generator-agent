"""main — entrypoint: orquesta intake → analysis → generator → validator.

run_pipeline() es el orquestador puro (testeable, sin I/O de consola);
main() es el wrapper interactivo fino.
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from src.agents.analysis_agent import run_analysis
from src.agents.generator_agent import run_generator
from src.agents.intake_agent import run_intake
from src.agents.validator_agent import ValidatorResult, run_validator


class PipelineResult(BaseModel):
    status: Literal["needs_input", "approved", "rejected"]
    questions: list[str] = []
    harness_path: Path | None = None
    generated_files: list[str] = []
    validator: ValidatorResult | None = None


def run_pipeline(text: str, mode: str, output_dir: Path) -> PipelineResult:
    intake = run_intake(text, mode)
    if intake.status == "needs_input":
        return PipelineResult(status="needs_input", questions=intake.questions)

    spec = run_analysis(intake.spec)
    harness_path = output_dir / "harness"
    generated = run_generator(spec, harness_path)
    verdict = run_validator(harness_path, spec)

    return PipelineResult(
        status="approved" if verdict.approved else "rejected",
        harness_path=harness_path,
        generated_files=generated,
        validator=verdict,
    )


def main() -> None:  # pragma: no cover — wrapper interactivo, sin lógica propia
    print("Modo del harness: [1] EJECUTOR  [2] PROFESOR")
    mode = "PROFESOR" if input("> ").strip() == "2" else "EJECUTOR"
    print("Describe tu proyecto:")
    text = input("> ")

    while True:
        result = run_pipeline(text, mode, Path.cwd())

        if result.status == "needs_input":
            print("Falta información sobre estas dimensiones:")
            for question in result.questions:
                print(f"  - {question}")
            print("Amplía la descripción:")
            text = f"{text} {input('> ')}"
            continue

        if result.status == "approved":
            print(f"Harness aprobado ✅ → {result.harness_path}")
            print(f"{len(result.generated_files)} ficheros generados.")
            return

        print("Harness rechazado ❌ — informe del validator:")
        for line in result.validator.informe:
            print(f"  - {line}")
        if input("¿Reintentar? [s/N] > ").strip().lower() != "s":
            return


if __name__ == "__main__":
    main()
