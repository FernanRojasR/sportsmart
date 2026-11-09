"""Colinealidad, selección, reducción de dimensionalidad, codificación, escalamiento y balanceo.

Se demuestra sobre el dataset de abandono, que tiene una variable objetivo. Todo se ajusta solo con
entrenamiento. Salida: reports/caracteristicas.json.  Uso:  python -m src.features.seleccion
"""
import json

import numpy as np
import pandas as pd
from imblearn.over_sampling import ADASYN, SMOTE, RandomOverSampler
from imblearn.under_sampling import RandomUnderSampler
from sklearn.compose import ColumnTransformer
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import recall_score, roc_auc_score
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, OneHotEncoder, StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src.config import PROCESSED, REPORTS, SEED

NOMINALES = ["genero", "zona", "canal_adquisicion", "deporte_preferido"]
EXCLUIR = ["cliente_id", "departamento", "edad_faltante", "abandona"]
UMBRAL_COLINEALIDAD = 0.85
COBERTURA_IMPORTANCIA = 0.90


def separar(df: pd.DataFrame):
    x = df.copy()
    x["edad"] = x.edad.mask(x.edad_faltante.astype(bool))  # se imputa de nuevo solo con entrenamiento
    y = x.abandona
    return train_test_split(x.drop(columns=EXCLUIR), y, test_size=.25, stratify=y, random_state=SEED)


def codificar(x_tr: pd.DataFrame, x_te: pd.DataFrame):
    """Mediana en numéricas y One-Hot en nominales, ajustados con entrenamiento."""
    num = [c for c in x_tr.columns if c not in NOMINALES]
    ct = ColumnTransformer([("num", SimpleImputer(strategy="median"), num), ("cat", OneHotEncoder(handle_unknown="ignore", drop="if_binary", sparse_output=False), NOMINALES)], verbose_feature_names_out=False).set_output(transform="pandas")
    return ct.fit_transform(x_tr).astype(float), ct.transform(x_te).astype(float), num


def eliminar_colinealidad(x: pd.DataFrame, y: pd.Series, umbral: float = UMBRAL_COLINEALIDAD):
    """Recorre los pares más correlacionados y retira la variable menos asociada con el objetivo."""
    corr = x.corr("spearman").abs(); con_y = x.corrwith(y, method="spearman").abs()
    pares = corr.where(np.triu(np.ones(corr.shape, dtype=bool), 1)).stack().sort_values(ascending=False)
    fuera, detalle = set(), []
    for (a, b), rho in pares[pares > umbral].items():
        if a in fuera or b in fuera:
            continue
        sale, queda = (a, b) if con_y[a] < con_y[b] else (b, a)
        fuera.add(sale); detalle.append({"retirada": sale, "conservada": queda, "rho": round(float(rho), 3)})
    return [c for c in x.columns if c not in fuera], detalle


def vif(x: pd.DataFrame) -> dict[str, float]:
    a = StandardScaler().fit_transform(x)
    return {c: round(float(variance_inflation_factor(a, i)), 2) for i, c in enumerate(x.columns)}


def _auc(modelo, x_tr, y_tr, x_te, y_te) -> dict[str, float]:
    modelo.fit(x_tr, y_tr); p = modelo.predict_proba(x_te)[:, 1]
    return {"auc": round(float(roc_auc_score(y_te, p)), 3), "recall": round(float(recall_score(y_te, p >= .5)), 3)}


def _logistica():
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))


def seleccion_importancia(x_tr, y_tr, cobertura=COBERTURA_IMPORTANCIA):
    rf = RandomForestClassifier(400, min_samples_leaf=5, class_weight="balanced", random_state=SEED, n_jobs=-1).fit(x_tr, y_tr)
    imp = pd.Series(rf.feature_importances_, x_tr.columns).sort_values(ascending=False)
    n = int((imp.cumsum() < cobertura).sum()) + 1
    return list(imp.index[:n]), imp


def balanceo(x_tr, y_tr, x_te, y_te) -> dict:
    tecnicas = {"Sin balanceo": None, "Undersampling": RandomUnderSampler(random_state=SEED), "Oversampling": RandomOverSampler(random_state=SEED), "SMOTE": SMOTE(random_state=SEED), "ADASYN": ADASYN(random_state=SEED)}
    esc = StandardScaler().fit(x_tr); a, b = pd.DataFrame(esc.transform(x_tr), columns=x_tr.columns), pd.DataFrame(esc.transform(x_te), columns=x_te.columns)
    r = {}
    for n, t in tecnicas.items():
        try:
            xb, yb = (a, y_tr) if t is None else t.fit_resample(a, y_tr)
        except ValueError as error:  # ADASYN no genera muestras si las clases ya están casi equilibradas
            r[n] = {"no_aplica": str(error)}
            continue
        cuentas = pd.Series(np.asarray(yb)).value_counts()
        r[n] = {"permanece": int(cuentas[0]), "abandona": int(cuentas[1]), **_auc(LogisticRegression(max_iter=2000), xb, yb, b, y_te)}
    return r


def atipicos_clientes(v: pd.DataFrame) -> dict:
    r = {}
    for c in ["recencia", "frecuencia", "monetario", "ticket_medio"]:
        s = v[c]; q1, q3 = s.quantile(.25), s.quantile(.75); w = q3 - q1
        r[c] = {"iqr": int(((s < q1 - 1.5 * w) | (s > q3 + 1.5 * w)).sum()), "z3": int((((s - s.mean()) / s.std()).abs() > 3).sum()), "asimetria": round(float(s.skew()), 2), "asimetria_log": round(float(np.log1p(s).skew()), 2)}
    return r


def escalamiento(v: pd.DataFrame) -> dict:
    x = v[["recencia", "frecuencia", "monetario"]]
    est, mm = pd.DataFrame(StandardScaler().fit_transform(x), columns=x.columns), pd.DataFrame(MinMaxScaler().fit_transform(x), columns=x.columns)
    return {c: {"original_max": round(float(x[c].max()), 2), "standard_media": round(float(est[c].mean()), 2) + 0.0, "standard_desv": round(float(est[c].std()), 2), "minmax_min": round(float(mm[c].min()), 2), "minmax_max": round(float(mm[c].max()), 2)} for c in x.columns}


def analizar(ab: pd.DataFrame, clientes: pd.DataFrame, productos: pd.DataFrame) -> dict:
    xtr0, xte0, ytr, yte = separar(ab)
    xtr, xte, num = codificar(xtr0, xte0)
    conservadas, retiradas = eliminar_colinealidad(xtr, ytr)
    sel, imp = seleccion_importancia(xtr[conservadas], ytr)
    rf = lambda: RandomForestClassifier(400, min_samples_leaf=5, class_weight="balanced", random_state=SEED, n_jobs=-1)
    numericas = [c for c in sel if c in num and xtr[c].nunique() > 2]
    pca = PCA(random_state=SEED).fit(StandardScaler().fit_transform(xtr[sel]))
    acum = np.cumsum(pca.explained_variance_ratio_); n90 = int((acum < .90).sum()) + 1
    le_abc = LabelEncoder().fit(productos.abc)
    return {
        "abandono": {"filas": len(ab), "tasa_abandono_pct": round(100 * float(ab.abandona.mean()), 1), "permanece": int((ab.abandona == 0).sum()), "abandona": int((ab.abandona == 1).sum()), "entrenamiento": len(xtr), "prueba": len(xte)},
        "codificacion": {"one_hot": {c: int(xtr0[c].nunique()) for c in NOMINALES}, "columnas_tras_one_hot": xtr.shape[1], "label_encoding_abc": {str(k): int(v) for k, v in zip(le_abc.classes_, le_abc.transform(le_abc.classes_))}},
        "escalamiento": escalamiento(clientes),
        "atipicos": atipicos_clientes(clientes),
        "colinealidad": {"umbral": UMBRAL_COLINEALIDAD, "columnas_antes": xtr.shape[1], "columnas_despues": len(conservadas), "retiradas": retiradas, "vif_max_antes": max(vif(xtr[[c for c in num if xtr[c].nunique() > 2]]).values()), "vif_despues": vif(xtr[[c for c in conservadas if c in num and xtr[c].nunique() > 2]])},
        "importancia": {"cobertura": COBERTURA_IMPORTANCIA, "n_seleccionadas": len(sel), "seleccionadas": sel, "importancias": {k: round(float(v), 4) for k, v in imp.items()}},
        "comparacion_variables": {"Todas": _auc(rf(), xtr, ytr, xte, yte), "Sin colinealidad": _auc(rf(), xtr[conservadas], ytr, xte[conservadas], yte), "Seleccionadas": _auc(rf(), xtr[sel], ytr, xte[sel], yte)},
        "reduccion": {"pca_varianza_acumulada": [round(float(a), 3) for a in acum], "pca_componentes_90": n90, "n_variables": len(sel),
                      "modelos": {"Logística con variables seleccionadas": _auc(_logistica(), xtr[sel], ytr, xte[sel], yte),
                                  "Logística con PCA (90 %)": _auc(make_pipeline(StandardScaler(), PCA(n90, random_state=SEED), LogisticRegression(max_iter=2000)), xtr[sel], ytr, xte[sel], yte),
                                  "LDA": _auc(make_pipeline(StandardScaler(), LinearDiscriminantAnalysis()), xtr[sel], ytr, xte[sel], yte),
                                  "QDA": _auc(make_pipeline(StandardScaler(), QuadraticDiscriminantAnalysis(reg_param=.1)), xtr[sel], ytr, xte[sel], yte)}, "numericas_continuas": numericas},
        "balanceo": balanceo(xtr[sel], ytr, xte[sel], yte),
        "abc_xyz": {"abc": productos.abc.value_counts().sort_index().to_dict(), "xyz": productos.xyz.value_counts().sort_index().to_dict(), "matriz": pd.crosstab(productos.abc, productos.xyz).to_dict("index"), "ingresos_pct_abc": {k: round(100 * float(v), 1) for k, v in (productos.groupby("abc").ingresos.sum() / productos.ingresos.sum()).items()}},
        "clientes": {"filas": len(clientes), "columnas": clientes.shape[1], "clv_mediana": round(float(clientes.clv.median()), 2), "clv_p90": round(float(clientes.clv.quantile(.9)), 2)},
    }


def main() -> dict:
    leer = lambda n: pd.read_csv(PROCESSED / f"{n}.csv")
    res = analizar(leer("abandono_dataset"), leer("clientes_variables"), leer("productos_abc_xyz"))
    (REPORTS / "caracteristicas.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    main()
