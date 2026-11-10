"""Ejecuta el pipeline completo desde la raíz del repo:

    python -m src.pipeline            # genera datos + EDA + diccionario
    python -m src.pipeline --sin-datos  # usa los CSV existentes en data/raw
"""
import runpy
import sys
from pathlib import Path

from src.evaluation import comparacion
from src.features import preparacion, seleccion, variables
from src.models import asociacion, clustering, grafos, regresion, series

PASOS = ["generar_dataset.py", "eda_calidad.py", "diccionario.py"]
BASE = Path(__file__).resolve().parent / "data"


def main() -> None:
    pasos = PASOS[1:] if "--sin-datos" in sys.argv else PASOS
    for paso in pasos:
        print(f"\n=== {paso} ===")
        runpy.run_path(str(BASE / paso), run_name="__main__")
    print("\n=== preparacion ===")
    preparacion.main()
    print("\n=== variables y selección ===")
    variables.main()
    seleccion.main()
    print("\n=== asociación ===")
    asociacion.main()
    print("\n=== clustering ===")
    clustering.main()
    print("\n=== series temporales ===")
    series.main()
    print("\n=== grafos ===")
    grafos.main()
    print("\n=== regresión ===")
    regresion.main()
    print("\n=== evaluación comparativa ===")
    comparacion.main()


if __name__ == "__main__":
    main()
