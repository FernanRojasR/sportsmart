"""Ejecuta el pipeline completo desde la raíz del repo:

    python -m src.pipeline            # genera datos + EDA + diccionario
    python -m src.pipeline --sin-datos  # usa los CSV existentes en data/raw
"""
import runpy
import sys
from pathlib import Path

PASOS = ["generar_dataset.py", "eda_calidad.py", "diccionario.py"]
BASE = Path(__file__).resolve().parent / "data"


def main() -> None:
    pasos = PASOS[1:] if "--sin-datos" in sys.argv else PASOS
    for paso in pasos:
        print(f"\n=== {paso} ===")
        runpy.run_path(str(BASE / paso), run_name="__main__")


if __name__ == "__main__":
    main()
