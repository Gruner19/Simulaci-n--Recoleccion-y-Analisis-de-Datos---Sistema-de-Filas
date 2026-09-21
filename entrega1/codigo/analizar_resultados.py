"""Sistema de manipulación y exportación de resultados del experimento fatorial 2^3.

Utilidades de línea de órdenes sobre los CSVs de salida del flujo de la Entrega 1:
lee, filtra, agrega, calcula efectos factoriales y ANOVA, y exporta a
CSV / Excel / JSON / LaTeX.

Uso general:
    python codigo/analizar_resultados.py <comando> [opciones]

Comandos:
    resumen    Estadísticas descriptivas del dataset cargado.
    filtrar    Aplica un filtro (expresión pandas) y exporta.
    agregar    Agrupa por factores y calcula media, desv., IC 95 %, CV y n.
    factorial  Estimación de efectos principales y de interacción (2^3) y % de contribución.
    anova      Tabla ANOVA (OLS sobre factores codificados y su interacción).
    listar     Enumerar los archivos de salida disponibles en datos/.

Formato de exportación: --formato csv|xlsx|json|latex  (por defecto csv).
Todos los comandos aceptan --salida; si no se da, se imprime por pantalla.
"""
from __future__ import annotations

import argparse
from itertools import combinations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DADOS, NIVEIS

FACTORES = ["A", "B", "C"]
RESULTADOS_POR_DEFECTO = DADOS / "resultados_fatorial.csv"


# ------------------------------------------------------------------ utilidades de carga / salida
def leer_resultados(ruta: Path) -> pd.DataFrame:
    ruta = Path(ruta)
    if not ruta.exists():
        sys.exit(f"No existe {ruta}. Ejecuta primero: "
                 f"python codigo/executar_experimento.py --force")
    df = pd.read_csv(ruta)
    return df


def br(x: float, d: int = 3) -> str:
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _df_from_json(datos: dict) -> pd.DataFrame:
    """Reconstruye un DataFrame desde {columnas, filas} (formato de la interfaz web)."""
    return pd.DataFrame(datos["filas"], columns=datos["columnas"])


def exportar(df: pd.DataFrame, ruta, formato: str, titulo: str = "") -> None:
    """Vuelca `df` a {ruta} en {formato}. Si ruta es None, imprime en pantalla."""
    if ruta is None:
        with pd.option_context("display.max_columns", 30, "display.width", 200,
                               "display.float_format", lambda v: f"{v:,.4f}"):
            print(df.to_string(index=False))
        return

    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if formato == "csv":
        df.to_csv(ruta, index=False)
    elif formato == "xlsx":
        try:
            df.to_excel(ruta, index=False, sheet_name="resultados")
        except ImportError:
            sys.exit("Falta 'openpyxl': pip install openpyxl (o usa --formato csv/json/latex).")
    elif formato == "json":
        ruta.write_text(df.to_json(orient="records", force_ascii=False, indent=2), encoding="utf-8")
    elif formato == "latex":
        ruta.write_text(_a_latex(df, titulo), encoding="utf-8")
    else:
        sys.exit(f"formato desconocido: {formato} (use csv|xlsx|json|latex)")
    print(f"Exportado -> {ruta}")


def _a_latex(df: pd.DataFrame, titulo: str) -> str:
    """Tabular LaTeX simple y autosuficiente (no depende de to_latex de pandas)."""
    cols = list(df.columns)
    tipos = df.dtypes.astype(str).tolist()
    alinea = ["r" if t in ("float64", "int64", "float32", "int32") else "l" for t in tipos]
    cab = " & ".join(_tex(c) for c in cols)
    filas = []
    for _, row in df.iterrows():
        celdas = []
        for c, t in zip(cols, tipos):
            v = row[c]
            if pd.isna(v):
                celdas.append("---")
            elif t in ("float64", "float32"):
                celdas.append(f"{float(v):.3f}".replace(".", ",").rjust(len(str(v)) + 3))
            else:
                celdas.append(_tex(str(v)))
        filas.append(" & ".join(celdas) + r" \\")
    body = "\n".join(filas) if filas else "\\multicolumn{{{n}}}{l}{{---}} \\\\".format(n=len(cols))
    tit = f" \\hline\n{_tex(titulo)}\n" if titulo else ""
    return (f"% Generado por codigo/analizar_resultados.py\n"
            f"\\begin{{tabular}}{{{''.join(alinea)}}}\n\\toprule\n{cab} \\\\\n\\midrule\n"
            f"{body}\n\\bottomrule\n\\end{{tabular}}\n")


def _tex(s: str) -> str:
    return (s.replace("_", "\\_").replace("%", "\\%").replace("#", "\\#")
             .replace("&", "\\&").replace("$", "\\$"))


def _porciento_ic(x: np.ndarray) -> tuple:
    from scipy import stats
    x = np.asarray(x, dtype=float)
    n = len(x)
    t = stats.t.ppf(0.975, n - 1)
    s = x.std(ddof=1)
    sem = s / np.sqrt(n)
    return x.mean(), x.mean() - t * sem, x.mean() + t * sem, s, sem


# ------------------------------------------------------------------ resumen
def resumen_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.describe(include="all").round(4)


def cmd_resumen(args):
    df = leer_resultados(args.entrada)
    extra = f"\nColumnas: {list(df.columns)}" if args.verboso else ""
    print(resumen_df(df).to_string())
    nomb = {f: NIVEIS[f]["nome"] for f in FACTORES if f in df.columns}
    if nomb:
        print("\nFactores y niveles (codificados):")
        for f, nom in nomb.items():
            print(f"  {f} ({nom}): {sorted(df[f].unique())}")
    print(extra)


# ------------------------------------------------------------------ filtrar
def filtrar_df(df: pd.DataFrame, donde) -> pd.DataFrame:
    return df.copy().query(donde) if donde else df.copy()


def cmd_filtrar(args):
    df = leer_resultados(args.entrada)
    sub = filtrar_df(df, args.donde)
    print(f"filtrar: {len(sub)}/{len(df)} filas cumplen '{args.donde or '(sin filtro)'}'")
    exportar(sub, args.salida, args.formato, f"Filtro: {args.donde}") if args.salida else (
        exportar(sub, None, "csv"))


# ------------------------------------------------------------------ agregar
def agregar_df(df: pd.DataFrame, por) -> pd.DataFrame:
    claves = [c for c in por if c in df.columns]
    df = df.copy()
    df["resposta"] = pd.to_numeric(df["resposta"], errors="coerce")
    agg = []
    for clave, grupo in df.groupby(claves, sort=False):
        x = grupo["resposta"].to_numpy()
        m, ic_inf, ic_sup, s, sem = _porciento_ic(x)
        if not isinstance(clave, tuple):
            clave = (clave,)
        fila = dict(zip(claves, clave))
        fila.update({"n": len(x), "media": m, "desv": s, "sem": sem,
                     "ic_inf": ic_inf, "ic_sup": ic_sup,
                     "cv_pct": 100 * s / m if m else np.nan})
        agg.append(fila)
    return pd.DataFrame(agg)


def cmd_agregar(args):
    out = agregar_df(leer_resultados(args.entrada), args.por)
    print(f"agregar: {len(out)} grupos")
    exportar(out, args.salida, args.formato, "Agregados por factores") if args.salida else (
        exportar(out, None, "csv"))


# ------------------------------------------------------------------ factorial 2^3
def factorial_df(df: pd.DataFrame, log: bool = False) -> pd.DataFrame:
    y = pd.to_numeric(df["resposta"], errors="coerce")
    if log:
        y = np.log(y)
    efectos = {}
    # combinatoria de efectos: principales y todas las interacciones
    for r in range(1, len(FACTORES) + 1):
        for bits in combinations(FACTORES, r):
            nombre = "".join(bits)
            plus = np.ones(len(y), bool)
            for f in bits:
                plus &= df[f] > 0
            menos = ~plus
            efectos[nombre] = float(y[plus].mean() - y[menos].mean())

    out = pd.DataFrame({"efecto": efectos.keys(),
                        "magnitud": list(efectos.values()),
                        "|m|_pct": [100 * abs(v) for v in efectos.values()]})
    total = out["|m|_pct"].sum()
    out["contribucion_pct"] = 100 * out["|m|_pct"] / total if total else 0
    return out


def cmd_factorial(args):
    escala = "logaría" if args.log else "unidades"
    out = factorial_df(leer_resultados(args.entrada), args.log)
    print(f"factorial 2^3 sobre resposta en escala {escala} (2 semas = magnitud):")
    print(out.round(4).to_string(index=False))
    if args.salida:
        exportar(out, args.salida, args.formato, f"Efectos factoriales (escala {escala})")


# ------------------------------------------------------------------ anova
def anova_df(df: pd.DataFrame, log: bool = False):
    import statsmodels.api as sm

    y = pd.to_numeric(df["resposta"], errors="coerce")
    if log:
        y = np.log(y)

    cols = FACTORES + ["AB", "AC", "BC", "ABC"]
    X = pd.DataFrame(index=df.index)
    for f in FACTORES:
        X[f] = df[f]
    for a, b in [("A", "B"), ("A", "C"), ("B", "C")]:
        X[a + b] = df[a] * df[b]
    X["ABC"] = df["A"] * df["B"] * df["C"]

    modelo = sm.OLS(y, sm.add_constant(X)).fit()
    tabla = pd.DataFrame({"efecto": ["Intercepto"] + cols,
                          "coef": modelo.params,
                          "se": modelo.bse,
                          "t": modelo.tvalues,
                          "p": modelo.pvalues})
    tabla["sig"] = np.where(tabla["p"] < 0.05, "*", "")
    return tabla, float(modelo.rsquared)


def cmd_anova(args):
    tabla, r2 = anova_df(leer_resultados(args.entrada), args.log)
    print(f"ANOVA OLS, resposta ~ factores codificados "
          f"{'(log)' if args.log else ''}  |  R2 = {r2:.4f}")
    print(tabla.round(4).to_string(index=False))
    if args.salida:
        exportar(tabla, args.salida, args.formato, f"ANOVA OLS (escala {'log' if args.log else 'unidades'})")


# ------------------------------------------------------------------ listar
def cmd_listar(args):
    archivos = sorted(DADOS.glob("*.csv"))
    if not archivos:
        sys.exit("No hay CSVs en datos/. Ejecuta la simulación primero.")
    for a in archivos:
        n = sum(1 for _ in a.open())
        print(f"{a.name:42s}  {n-1:>7,} filas")
    if args.verboso:
        print("\nNota: el flujo completo es  plano -> verificacion -> piloto -> experimento.")


# ------------------------------------------------------------------ informe completo
def cmd_informe(args):
    """Composa un informe consolidado (Markdown) + los CSVs/teX de los análisis."""
    import datetime as _dt

    carpeta = Path(args.salida) if args.salida else DADOS
    carpeta.mkdir(parents=True, exist_ok=True)
    fragmentos = []

    # ---- facturas primarias ----
    if (DADOS / "verificacao_simulador.csv").exists():
        v = pd.read_csv(DADOS / "verificacao_simulador.csv")
        f = carpeta / "informe_verificacion.csv"
        v.round(4).to_csv(f, index=False)
        fragmentos.append("## 1. Verificación del simulador vs. teoría\n")
        max_e = v.erro_rel_pct.abs().max()
        fragmentos.append(f"Error relativo máximo = **{max_e:.2f}%**.\n\n"
                          f"| c | λ | serviço | simulado | teórico | err% |\n"
                          f"|---|----|---------|----------|---------|------|\n")
        for _, r in v.iterrows():
            fragmentos.append(f"| {int(r.c)} | {r['lambda']} | {r.servico} | {r.media_simulada:.4f} "
                              f"| {r.teorico:.4f} | {r.erro_rel_pct:.2f} |\n")
        fragmentos.append("\n")

    # ---- experimento: agregados por célula ----
    df = leer_resultados(args.entrada)
    agg = []
    for cel, g in df.groupby("celula", sort=False):
        x = pd.to_numeric(g["resposta"], errors="coerce").to_numpy()
        m, lo, hi, s, sem = _porciento_ic(x)
        agg.append({"celula": int(cel), "n": len(x), "media": m, "desv": s,
                    "ic_inf": lo, "ic_sup": hi, "cv_pct": 100 * s / m})
    ag = pd.DataFrame(agg)
    ag.round(4).to_csv(carpeta / "informe_resumen_celulas.csv", index=False)
    fragmentos.append("## 2. Experimento fatorial 2^3 — resumen por célula (r = 10)\n\n")
    fragmentos.append("| cel | n | media | desv | IC95 inf | IC95 sup | CV% |\n"
                      "|-----|---|-------|------|----------|----------|-----|\n")
    for _, r in ag.iterrows():
        fragmentos.append(f"| {int(r.celula)} | {int(r.n)} | {r.media:.4f} | {r.desv:.4f} "
                          f"| {r.ic_inf:.4f} | {r.ic_sup:.4f} | {r.cv_pct:.2f} |\n")
    fragmentos.append("\n")

    # ---- efectos factoriales y ANOVA ----
    y = pd.to_numeric(df["resposta"], errors="coerce")
    yl = np.log(y)
    efectos = {}
    for r in range(1, len(FACTORES) + 1):
        for bits in combinations(FACTORES, r):
            nm = "".join(bits)
            plus = np.ones(len(yl), bool)
            for f in bits:
                plus &= df[f] > 0
            efectos[nm] = float(yl[plus].mean() - yl[~plus].mean())
    ef = pd.DataFrame({"efecto": list(efectos.keys()),
                       "magnitud(log)": [efectos[k] for k in efectos]})
    ef.round(4).to_csv(carpeta / "informe_efectos.csv", index=False)
    fragmentos.append("## 3. Efectos del fatorial 2^3 (sobre log(resposta))\n\n")
    fragmentos.append("| efecto | magnitud(log) |\n|--------|---------------|\n")
    for _, r in ef.iterrows():
        fragmentos.append(f"| {r['efecto']} | {r['magnitud(log)']:.4f} |\n")
    fragmentos.append("\n")

    # ---- método / reproducción ----
    fragmentos.append("## 4. Reproducción\n\n")
    fragmentos.append("```\n"
                      "python3 -m venv .venv && .venv/bin/pip install -r codigo/requirements.txt\n"
                      "make dados experimento\n"
                      "make resultados\n"
                      "```\n")
    fragmentos.append(f"*Fecha de generación*: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    md = "# Resultados — Entrega 1\n\n" + "".join(fragmentos)
    ruta_md = carpeta / (args.nombre if args.nombre else "resultados_resumen.md")
    ruta_md.write_text(md, encoding="utf-8")
    print(f"Informe generado -> {ruta_md}")
    print(md)


# ------------------------------------------------------------------ CLI
def main():
    ap = argparse.ArgumentParser(prog="analizar_resultados", description=__doc__.splitlines()[0])
    ap.add_argument("-v", "--verboso", action="store_true", help="salida más detallada")
    sub = ap.add_subparsers(dest="cmd", required=True)

    comunes = argparse.ArgumentParser(add_help=False)
    comunes.add_argument("--entrada", default=str(RESULTADOS_POR_DEFECTO))
    comunes.add_argument("--salida", default=None, help="ruta de salida (si se omite, imprime)")
    comunes.add_argument("--formato", choices=["csv", "xlsx", "json", "latex"], default="csv")

    p = sub.add_parser("resumen", parents=[comunes], help="estadísticas del dataset")
    p.set_defaults(fn=cmd_resumen)

    p = sub.add_parser("filtrar", parents=[comunes], help="filtra y exporta")
    p.add_argument("--donde", required=True, help="expresión pandas, p. ej. 'celula==2 & replica>=5'")
    p.set_defaults(fn=cmd_filtrar)

    p = sub.add_parser("agregar", parents=[comunes], help="agrupa y agrega por factores")
    p.add_argument("-p", "--por", nargs="+", default=["celula"], help="factores de agrupación")
    p.set_defaults(fn=cmd_agregar)

    p = sub.add_parser("factorial", parents=[comunes], help="efectos del fatorial 2^3")
    p.add_argument("--log", action="store_true", help="usa log(resposta)")
    p.set_defaults(fn=cmd_factorial)

    p = sub.add_parser("anova", parents=[comunes], help="tabla ANOVA (OLS)")
    p.add_argument("--log", action="store_true", help="usa log(resposta)")
    p.set_defaults(fn=cmd_anova)

    p = sub.add_parser("listar", help="lista los CSVs de datos/")
    p.set_defaults(fn=cmd_listar)

    p = sub.add_parser("informe", parents=[comunes], help="informe consolidado (MD + CSVs)")
    p.add_argument("--nombre", default=None, help="nombre del archivo .md (def.: resultados_resumen.md)")
    p.set_defaults(fn=cmd_informe)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()