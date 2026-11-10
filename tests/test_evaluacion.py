"""Pruebas de la evaluación comparativa. Ejecutar: pytest -q"""
import numpy as np
import pandas as pd

from src.evaluation.comparacion import REF_SERIES, _intervalo, bootstrap_series, leer, metas_no_alcanzadas, respuestas, tabla_resultados

REPORTES = ("asociacion", "clustering", "series", "grafos", "regresion")


def _r():
    return {n: leer(n) for n in REPORTES}


def test_intervalo_ordenado():
    a, b = _intervalo(np.arange(100.0))
    assert a < b


def test_tabla_cubre_las_cinco_tecnicas_y_las_metas():
    t = tabla_resultados(_r(), {"asociacion": {"reglas_azar_media": 0.0}, "clustering": {"silhouette": 0.2}})
    assert [f["tecnica"] for f in t] == ["Asociación", "Clustering", "Series temporales", "Grafos", "Regresión"]
    assert all(f["cumple"] and f["supera_referencia"] for f in t)


def test_supera_referencia_respeta_el_sentido_de_la_metrica():
    t = {f["tecnica"]: f for f in tabla_resultados(_r(), {"asociacion": {"reglas_azar_media": 0.0}, "clustering": {"silhouette": 0.9}})}
    assert t["Series temporales"]["mejor_si"] == "menor" and t["Series temporales"]["resultado"] < t["Series temporales"]["referencia"]
    assert not t["Clustering"]["supera_referencia"]


def test_bootstrap_detecta_un_modelo_mejor():
    idx = pd.date_range("2024-01-01", periods=70, freq="D")
    rng = np.random.default_rng(1); real = 1000 + rng.normal(0, 30, 70)
    r = bootstrap_series({"fechas": [str(d.date()) for d in idx], "real": real.tolist(), "Prophet": (real * 1.01).tolist(), REF_SERIES: (real * 1.3).tolist()})
    assert r["mejora_puntos_ic95"][0] > 0


def test_se_reportan_los_resultados_bajo_lo_esperado():
    assert len(metas_no_alcanzadas(_r())) == 3


def test_respuestas_excluyen_preguntas_de_semana_16():
    assert not {x["n"] for x in respuestas(_r())} & {"12", "13", "16", "17", "18"}


def test_graficos_se_generan(tmp_path):
    from src.evaluation import graficos
    rutas = graficos.main(tmp_path)
    assert [r.name for r in rutas] == ["regresion_validacion_prueba.png", "regresion_factores_detalle.png", "evaluacion_comparativa.png"]
    assert all(r.stat().st_size > 10_000 for r in rutas)
