"""main — entrypoint: orquesta intake → analysis → generator → validator.

run_pipeline() es el orquestador puro (testeable, sin I/O de consola);
main() despacha a _run_noninteractive() (con --text, para agentes vía Bash)
o _run_interactive() (sin --text, wrapper interactivo para un humano).
"""

import argparse
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from src.agents.analysis_agent import run_analysis
from src.agents.generator_agent import run_generator
from src.agents.intake_agent import run_intake
from src.agents.validator_agent import ValidatorResult, run_validator
from src.tools.inspect_project import inspect_project


class PipelineResult(BaseModel):
    status: Literal["needs_input", "approved", "rejected"]
    questions: list[str] = []
    harness_path: Path | None = None
    generated_files: list[str] = []
    validator: ValidatorResult | None = None


def run_pipeline(text: str, mode: str, output_dir: Path) -> PipelineResult:
    inspection = inspect_project(output_dir)
    intake = run_intake(text, mode, inspection)
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


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera un harness multi-agente personalizado para Claude Code.",
    )
    parser.add_argument(
        "--text",
        default=None,
        help="Descripción del proyecto. Si se da, arranca en modo no interactivo "
             "(sin input()) — pensado para invocarse desde un agente vía Bash.",
    )
    parser.add_argument(
        "--mode",
        choices=["EJECUTOR", "PROFESOR"],
        default="EJECUTOR",
        help="Modo del harness. Solo aplica junto a --text.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directorio destino. Solo aplica junto a --text (por defecto, el cwd actual).",
    )
    return parser.parse_args(argv)


def _run_noninteractive(text: str, mode: str, output_dir: Path) -> None:
    result = run_pipeline(text, mode, output_dir)

    if result.status == "needs_input":
        print("Falta información sobre estas dimensiones:")
        for question in result.questions:
            print(f"  - {question}")
        print("Vuelve a invocar con --text incluyendo esta información.")
        raise SystemExit(1)

    if result.status == "approved":
        print(f"Harness aprobado ✅ → {result.harness_path}")
        print(f"{len(result.generated_files)} ficheros generados.")
        return

    print("Harness rechazado ❌ — informe del validator:")
    for line in result.validator.informe:
        print(f"  - {line}")
    raise SystemExit(1)


def _run_interactive() -> None:  # pragma: no cover — wrapper interactivo, sin lógica propia
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


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if args.text is not None:
        _run_noninteractive(args.text, args.mode, args.output_dir or Path.cwd())
        return

    _run_interactive()


if __name__ == "__main__":
    main()
