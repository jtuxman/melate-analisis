#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analisis_melate.py — Análisis estadístico de la lotería Melate, Revancha y Revanchita.

Regenera el reporte completo (frecuencias, patrones combinatorios y evolución de la
bolsa) a partir de los CSV oficiales. Pensado para volver a ejecutarse cada vez que
actualices los archivos con sorteos nuevos: ordena por concurso y recalcula todo solo.

Uso:
    python3 analisis_melate.py                  # imprime el reporte en la terminal
    python3 analisis_melate.py -o reporte.md    # guarda el reporte en un archivo .md
    python3 analisis_melate.py --juego Melate   # analiza solo un juego
    python3 analisis_melate.py --dir /ruta/csv  # carpeta donde están los CSV
    python3 analisis_melate.py --desde 2010-01-01   # cambia el inicio del periodo
    python3 analisis_melate.py --grafico        # además genera evolucion_bolsa.png
    python3 analisis_melate.py --combinaciones 10   # 10 sextetas que respetan los patrones

Requisitos: Python 3.8+, pandas, numpy.
Opcionales: scipy (añade el p-value del χ²), matplotlib (necesario solo para --grafico).

Correcciones de datos incorporadas (ver el reporte estático para el detalle):
  - Reconversión monetaria de 1993: los concursos <= 528 estaban en pesos viejos y se
    dividen entre 1000 para compararlos en pesos de hoy.
  - BOLSA = 0 es un dato faltante, no una bolsa real: se trata como nulo.
  - El rango de números del Melate cambió con los años; las frecuencias se calculan
    solo desde 2007 (formato estable 1-56).
"""
from __future__ import annotations

import argparse
import datetime as dt
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Configuración
# --------------------------------------------------------------------------- #
JUEGOS = {
    "Melate":     {"archivo": "Melate.csv",     "nums": ["R1", "R2", "R3", "R4", "R5", "R6"], "adicional": "R7"},
    "Revancha":   {"archivo": "Revancha.csv",   "nums": ["R1", "R2", "R3", "R4", "R5", "R6"], "adicional": None},
    "Revanchita": {"archivo": "Revanchita.csv", "nums": ["F1", "F2", "F3", "F4", "F5", "F6"], "adicional": None},
}

DESDE_DEFAULT   = "2007-01-01"  # inicio del formato estable 1-56
RECONV_CONCURSO = 528           # concursos <= este: pesos viejos (dividir entre 1000)
N_BOMBO         = 56            # números del bombo (formato actual)
K_SORTEO        = 6             # números principales por sorteo
UMBRAL_REINICIO = 0.15          # caída de bolsa > 15% => hubo ganador del premio mayor
CHI2_CRIT_55    = 73.31         # valor crítico chi-cuadrado, gl=55, alfa=5%
MILLON          = 1_000_000


# --------------------------------------------------------------------------- #
# Carga y limpieza
# --------------------------------------------------------------------------- #
def cargar(cfg: dict, carpeta: Path) -> pd.DataFrame:
    """Lee un CSV, parsea fechas, ordena por concurso y normaliza la bolsa."""
    ruta = carpeta / cfg["archivo"]
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")
    df = pd.read_csv(ruta)

    faltan = [c for c in cfg["nums"] + ["CONCURSO", "BOLSA", "FECHA"] if c not in df.columns]
    if faltan:
        raise ValueError(f"{cfg['archivo']}: faltan columnas {faltan}. Columnas: {list(df.columns)}")

    df["FECHA"] = pd.to_datetime(df["FECHA"], format="%d/%m/%Y", errors="coerce")
    df = df.sort_values("CONCURSO").reset_index(drop=True)
    df["AÑO"] = df["FECHA"].dt.year

    # Bolsa en pesos de hoy; los ceros son datos faltantes, no bolsas reales.
    df["BOLSA_N"] = np.where(df["CONCURSO"] <= RECONV_CONCURSO, df["BOLSA"] / 1000, df["BOLSA"]).astype(float)
    df.loc[df["BOLSA"] == 0, "BOLSA_N"] = np.nan
    return df


# --------------------------------------------------------------------------- #
# Utilidades de formato Markdown
# --------------------------------------------------------------------------- #
def md_tabla(headers: list[str], filas: list[list]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for f in filas:
        out.append("| " + " | ".join(str(x) for x in f) + " |")
    return out


def _periodo(df: pd.DataFrame, desde: str) -> pd.DataFrame:
    return df[df["FECHA"] >= pd.Timestamp(desde)]


# --------------------------------------------------------------------------- #
# Secciones del reporte
# --------------------------------------------------------------------------- #
def seccion_resumen(df: pd.DataFrame, nombre: str, cfg: dict) -> list[str]:
    nulos = int(df[["CONCURSO"] + cfg["nums"]].isna().any(axis=1).sum())
    dups = int(df["CONCURSO"].duplicated().sum())
    extra = f" + {cfg['adicional']} (adicional)" if cfg["adicional"] else ""
    return [
        f"### {nombre}", "",
        f"- Sorteos: **{len(df):,}** · números: {', '.join(cfg['nums'])}{extra}",
        f"- Concursos: {int(df['CONCURSO'].min())} → {int(df['CONCURSO'].max())}",
        f"- Fechas: {df['FECHA'].min():%d/%m/%Y} → {df['FECHA'].max():%d/%m/%Y}",
        f"- Calidad: {nulos} filas con nulos · {dups} concursos duplicados",
        "",
    ]


def seccion_frecuencias(df: pd.DataFrame, nombre: str, cfg: dict, desde: str) -> list[str]:
    sub = _periodo(df, desde)
    n = len(sub)
    if n == 0:
        return [f"### {nombre}", "", "_Sin datos en el periodo._", ""]

    freq = (pd.Series(Counter(sub[cfg["nums"]].values.ravel()))
            .reindex(range(1, N_BOMBO + 1), fill_value=0).sort_index())
    esperado = n * K_SORTEO / N_BOMBO
    chi2 = float((((freq - esperado) ** 2) / esperado).sum())
    desv = (freq - esperado) / esperado * 100

    cal = freq.sort_values(ascending=False).head(8)
    fri = freq.sort_values().head(8)
    f_cal = ", ".join(f"{i} ({desv[i]:+.0f}%)" for i in cal.index)
    f_fri = ", ".join(f"{i} ({desv[i]:+.0f}%)" for i in fri.index)

    veredicto = "compatible con azar ✅" if chi2 < CHI2_CRIT_55 else "posible sesgo ⚠️"
    pval = ""
    try:  # scipy es opcional
        from scipy.stats import chi2 as _chi2
        pval = f", p={1 - _chi2.cdf(chi2, N_BOMBO - 1):.2f}"
    except Exception:
        pass

    return [
        f"### {nombre}", "",
        f"- Sorteos desde {desde}: **{n:,}** · frecuencia esperada por número: {esperado:.1f}",
        f"- **χ² = {chi2:.1f}** (gl={N_BOMBO - 1}, crítico 5% ≈ {CHI2_CRIT_55}{pval}) → **{veredicto}**",
        f"- Más frecuentes: {f_cal}",
        f"- Menos frecuentes: {f_fri}",
        "",
    ] + seccion_atrasos(sub, cfg)


def seccion_atrasos(sub: pd.DataFrame, cfg: dict) -> list[str]:
    """Sorteos transcurridos desde la última aparición de cada número."""
    n = len(sub)
    if n == 0:
        return []
    arr = sub[cfg["nums"]].to_numpy()
    pos = {x: -1 for x in range(1, N_BOMBO + 1)}
    for i in range(n):
        for num in arr[i]:
            pos[int(num)] = i
    atraso = {x: (n - 1 - p if p >= 0 else n) for x, p in pos.items()}
    top = sorted(atraso.items(), key=lambda kv: kv[1], reverse=True)[:6]
    return [f"- Mayor atraso (sorteos sin salir, al último sorteo): "
            + ", ".join(f"{num} ({g})" for num, g in top), ""]


def seccion_patrones(df: pd.DataFrame, nombre: str, cfg: dict, desde: str) -> list[str]:
    sub = _periodo(df, desde)
    n = len(sub)
    if n == 0:
        return []
    mat = sub[cfg["nums"]].to_numpy()
    pares = (mat % 2 == 0).sum(axis=1)
    bajos = (mat <= N_BOMBO // 2).sum(axis=1)
    sumas = mat.sum(axis=1)
    cp = Counter(pares)
    dist = " · ".join(f"{k}p {cp.get(k, 0) / n * 100:.0f}%" for k in range(K_SORTEO + 1))
    return [
        f"**{nombre}**",
        f"- Pares por sorteo (de {K_SORTEO}): {dist}",
        f"- Bajos (1–{N_BOMBO // 2}) vs altos: media {bajos.mean():.2f} bajos (lo común: 3/3)",
        f"- Suma de los {K_SORTEO}: media {sumas.mean():.0f}, mediana {np.median(sumas):.0f}, "
        f"rango [{sumas.min()}–{sumas.max()}], 80% central [{np.percentile(sumas, 10):.0f}–{np.percentile(sumas, 90):.0f}]",
        "",
    ]


def seccion_bolsa(df: pd.DataFrame, nombre: str) -> list[str]:
    dfb = df.dropna(subset=["BOLSA_N"])
    if dfb.empty:
        return [f"### {nombre}", "", "_Sin datos de bolsa._", ""]

    L = [f"### {nombre}", "", "**Mayores acumulados (corregidos a pesos de hoy):**", ""]
    top = dfb.nlargest(3, "BOLSA_N")
    L += md_tabla(["Concurso", "Fecha", "Bolsa"],
                  [[int(r.CONCURSO), f"{r.FECHA:%d/%m/%Y}", f"${r.BOLSA_N / MILLON:,.1f} M"] for r in top.itertuples()])
    L += [""]

    # Evolución por quinquenio
    tmp = dfb.copy()
    tmp["Q"] = (tmp["AÑO"] // 5) * 5
    g = tmp.groupby("Q")["BOLSA_N"].agg(["mean", "max", "count"])
    L += ["**Evolución de la bolsa por quinquenio:**", ""]
    L += md_tabla(["Periodo", "Promedio", "Máximo", "Sorteos"],
                  [[f"{int(q)}–{int(q) + 4}", f"${row['mean'] / MILLON:,.0f} M",
                    f"${row['max'] / MILLON:,.0f} M", int(row["count"])] for q, row in g.iterrows()])
    L += [""]

    # Dinámica de acumulación sobre el tramo continuo (después del último faltante)
    ult_cero = df.loc[df["BOLSA"] == 0, "CONCURSO"].max()
    corte = ult_cero if pd.notna(ult_cero) else -1
    cont = df[df["CONCURSO"] > corte].dropna(subset=["BOLSA_N"]).reset_index(drop=True)
    if len(cont) > 2:
        b = cont["BOLSA_N"].to_numpy()
        rein = b < np.roll(b, 1) * (1 - UMBRAL_REINICIO)
        rein[0] = False
        n_rein = int(rein.sum())
        bordes = np.concatenate([[0], np.where(rein)[0], [len(b)]])
        rachas = np.diff(bordes)
        j = int(np.argmax(rachas))
        ini, fin = bordes[j], bordes[j + 1] - 1
        L += ["**Dinámica de acumulación (tramo continuo):**", "",
              f"- Periodo: concurso {int(cont['CONCURSO'].min())}+ "
              f"({cont['FECHA'].min():%d/%m/%Y}) · {len(cont):,} sorteos",
              f"- Premios mayores repartidos: {n_rein} → en promedio cada "
              f"{len(cont) / max(n_rein, 1):.1f} sorteos",
              f"- Racha media: {rachas.mean():.1f} sorteos · **más larga: {int(rachas.max())} sorteos** sin ganador",
              f"  (de ${cont.iloc[ini]['BOLSA_N'] / MILLON:,.0f} M a ${cont.iloc[fin]['BOLSA_N'] / MILLON:,.0f} M, "
              f"{cont.iloc[ini]['FECHA']:%b/%Y} → {cont.iloc[fin]['FECHA']:%b/%Y})",
              ""]

    ult = dfb.iloc[-1]
    L += [f"- **Estado actual** (concurso {int(ult['CONCURSO'])}, {ult['FECHA']:%d/%m/%Y}): "
          f"bolsa de **${ult['BOLSA_N'] / MILLON:,.1f} millones**", ""]
    return L


# --------------------------------------------------------------------------- #
# Gráfico de evolución de la bolsa (los tres juegos; requiere matplotlib)
# --------------------------------------------------------------------------- #
def generar_grafico(carpeta: Path, ruta_png: str, desde_serie: str = "2009-01-01") -> None:
    """Guarda un PNG con la evolución de la bolsa: serie temporal de los tres juegos
    (patrón acumulación→reinicio) y máximo anual de Melate (tendencia de fondo)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.ticker import FuncFormatter
    except ImportError:
        print("⚠ matplotlib no está instalado; se omite el gráfico. "
              "Instálalo con:  pip install matplotlib")
        return

    colores = {"Melate": "#1f77b4", "Revancha": "#d62728", "Revanchita": "#2ca02c"}
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9),
                                   gridspec_kw={"height_ratios": [2.3, 1]})

    # Panel 1: serie temporal de los tres juegos.
    cache = {}
    for nombre, cfg in JUEGOS.items():
        df = cargar(cfg, carpeta).dropna(subset=["BOLSA_N"])
        cache[nombre] = df
        if df.empty:
            continue
        color = colores.get(nombre)
        d = df[df["FECHA"] >= pd.Timestamp(desde_serie)]
        ax1.plot(d["FECHA"], d["BOLSA_N"] / MILLON, color=color, lw=0.9, label=nombre)
        rec = df.loc[df["BOLSA_N"].idxmax()]
        ax1.scatter([rec["FECHA"]], [rec["BOLSA_N"] / MILLON], color=color, s=45,
                    zorder=5, edgecolor="white", linewidth=0.8)
        ax1.annotate(f"récord ${rec['BOLSA_N'] / MILLON:,.0f} M\n{rec['FECHA']:%b %Y}",
                     (rec["FECHA"], rec["BOLSA_N"] / MILLON), textcoords="offset points",
                     xytext=(6, 6), fontsize=8, color=color, fontweight="bold")

    ax1.set_title(f"Evolución de la bolsa — Melate, Revancha y Revanchita "
                  f"(pesos de hoy, desde {desde_serie[:4]})", fontsize=13, fontweight="bold")
    ax1.set_ylabel("Bolsa acumulada (millones $)")
    ax1.legend(loc="upper left", framealpha=0.9)
    ax1.grid(alpha=0.25)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax1.set_ylim(bottom=0)

    # Panel 2: máximo anual de Melate (deja ver la tendencia que los dientes esconden).
    dfm = cache.get("Melate")
    if dfm is not None and not dfm.empty:
        maxan = (dfm.groupby("AÑO")["BOLSA_N"].max() / MILLON)
        maxan = maxan[maxan.index >= 1995]
        ax2.bar(maxan.index, maxan.values, color=colores["Melate"], alpha=0.85)
        ax2.axvspan(2006.5, 2007.5, color="orange", alpha=0.2)
        ax2.annotate("formato 1–56\n(2007)", (2007, maxan.max() * 0.9), fontsize=8,
                     ha="center", color="darkorange")
        ax2.set_title("Melate: bolsa máxima alcanzada cada año", fontsize=11)
        ax2.set_ylabel("Máximo (millones $)")
        ax2.set_xlabel("Año")
        ax2.grid(alpha=0.25, axis="y")

    fig.tight_layout()
    fig.savefig(ruta_png, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Gráfico guardado en: {ruta_png}")


# --------------------------------------------------------------------------- #
# Generador de combinaciones que respetan los patrones del histórico
# --------------------------------------------------------------------------- #
def _resolver_juego(nombre: str) -> str:
    match = next((k for k in JUEGOS if k.lower() == nombre.lower()), None)
    if match is None:
        raise SystemExit(f"Juego desconocido: {nombre!r}. Opciones: {', '.join(JUEGOS)}")
    return match


def generar_combinaciones(df: pd.DataFrame, cfg: dict, desde: str, n: int = 10,
                          cobertura: float = 0.80, seed: int | None = None):
    """Genera n sextetas distintas (sin repetir números) que caen dentro de los patrones
    típicos del histórico: suma en el 80% central, y composiciones de pares/impares y
    bajos/altos que cubren el `cobertura` de los sorteos. NO usa "calientes/fríos" (ruido)
    y NO mejora la probabilidad de ganar: cada sexteta es equiprobable."""
    sub = _periodo(df, desde)
    if sub.empty:
        raise SystemExit(f"No hay sorteos desde {desde} para derivar los patrones.")
    mat = sub[cfg["nums"]].to_numpy()
    sumas = mat.sum(axis=1)
    pares_hist = pd.Series((mat % 2 == 0).sum(axis=1))
    bajos_hist = pd.Series((mat <= N_BOMBO // 2).sum(axis=1))

    def comp_tipica(serie: pd.Series) -> set[int]:
        """Conjunto mínimo de composiciones más frecuentes que cubren `cobertura`."""
        vc = serie.value_counts(normalize=True).sort_values(ascending=False)
        acc, keep = 0.0, set()
        for val, frac in vc.items():
            keep.add(int(val))
            acc += frac
            if acc >= cobertura:
                break
        return keep

    smin, smax = int(np.percentile(sumas, 10)), int(np.percentile(sumas, 90))
    pares_ok, bajos_ok = comp_tipica(pares_hist), comp_tipica(bajos_hist)

    rng = np.random.default_rng(seed)
    universo = np.arange(1, N_BOMBO + 1)
    combos, vistos = [], set()
    intentos, tope = 0, max(n * 100_000, 1_000_000)
    while len(combos) < n and intentos < tope:
        intentos += 1
        c = tuple(sorted(int(x) for x in rng.choice(universo, size=K_SORTEO, replace=False)))
        if c in vistos:
            continue
        npar = sum(1 for x in c if x % 2 == 0)
        nbaj = sum(1 for x in c if x <= N_BOMBO // 2)
        if smin <= sum(c) <= smax and npar in pares_ok and nbaj in bajos_ok:
            vistos.add(c)
            combos.append((c, sum(c), npar, nbaj))

    crit = {"suma": (smin, smax), "pares_ok": sorted(pares_ok), "bajos_ok": sorted(bajos_ok)}
    return combos, crit


# --------------------------------------------------------------------------- #
# Ensamblado del reporte
# --------------------------------------------------------------------------- #
def construir_reporte(carpeta: Path, desde: str, solo_juego: str | None = None) -> str:
    juegos = {k: v for k, v in JUEGOS.items()
              if solo_juego is None or k.lower() == solo_juego.lower()}
    if not juegos:
        raise SystemExit(f"Juego desconocido: {solo_juego!r}. Opciones: {', '.join(JUEGOS)}")

    dfs = {k: cargar(v, carpeta) for k, v in juegos.items()}
    hoy = dt.date.today().strftime("%d/%m/%Y")

    L = [
        "# Reporte de análisis — Lotería Melate", "",
        f"- Generado: {hoy}",
        f"- Periodo de frecuencias: desde {desde} (formato estable 1–{N_BOMBO})",
        "",
        "> Análisis estadístico con fines educativos. La lotería es un juego de azar; "
        "ningún resultado aquí mejora la probabilidad de ganar.",
        "", "---", "",
        "## 1. Resumen de los datos", "",
    ]
    for k, df in dfs.items():
        L += seccion_resumen(df, k, juegos[k])

    L += ["---", "", "## 2. Frecuencias, atraso y test de uniformidad (χ²)", ""]
    for k, df in dfs.items():
        L += seccion_frecuencias(df, k, juegos[k], desde)

    L += ["---", "", "## 3. Patrones combinatorios", ""]
    for k, df in dfs.items():
        L += seccion_patrones(df, k, juegos[k], desde)

    L += ["---", "", "## 4. Evolución de la bolsa", ""]
    for k, df in dfs.items():
        L += seccion_bolsa(df, k)

    L += ["---", "",
          f"_Generado por `analisis_melate.py`. Correcciones: concursos ≤ {RECONV_CONCURSO} "
          "÷1000 (reconversión 1993); BOLSA=0 tratada como dato faltante._"]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Análisis estadístico de la lotería Melate / Revancha / Revanchita.")
    ap.add_argument("--dir", default=None,
                    help="Carpeta con los CSV (default: la carpeta de este script).")
    ap.add_argument("-o", "--output",
                    help="Archivo .md de salida (si se omite, imprime en pantalla).")
    ap.add_argument("--desde", default=DESDE_DEFAULT,
                    help=f"Fecha inicial (YYYY-MM-DD) para frecuencias (default {DESDE_DEFAULT}).")
    ap.add_argument("--juego", help="Analizar solo un juego: Melate | Revancha | Revanchita.")
    ap.add_argument("--grafico", nargs="?", const="evolucion_bolsa.png", default=None,
                    metavar="ARCHIVO.png",
                    help="Genera un PNG con la evolución de la bolsa (los 3 juegos siempre). "
                         "Default: evolucion_bolsa.png. Requiere matplotlib.")
    ap.add_argument("--combinaciones", type=int, metavar="N",
                    help="Genera N sextetas que respetan los patrones del histórico "
                         "(suma, pares/impares, bajos/altos). NO mejora la probabilidad de ganar.")
    ap.add_argument("--seed", type=int, default=None,
                    help="Semilla aleatoria para reproducir las mismas combinaciones.")
    args = ap.parse_args()

    carpeta = Path(args.dir).expanduser().resolve() if args.dir else Path(__file__).resolve().parent

    # Modo "combinaciones": genera sextetas que respetan los patrones del histórico.
    if args.combinaciones:
        juego = _resolver_juego(args.juego) if args.juego else "Melate"
        combos, crit = generar_combinaciones(
            cargar(JUEGOS[juego], carpeta), JUEGOS[juego], args.desde,
            args.combinaciones, seed=args.seed)
        smin, smax = crit["suma"]
        print(f"\n{len(combos)} combinaciones para {juego} que respetan los patrones del "
              f"histórico (desde {args.desde}):")
        print(f"  criterios derivados: suma {smin}–{smax} · pares en {crit['pares_ok']} · "
              f"bajos(1–{N_BOMBO // 2}) en {crit['bajos_ok']}\n")
        for i, (c, s, npar, nbaj) in enumerate(combos, 1):
            nums = "  ".join(f"{x:02d}" for x in c)
            print(f"  {i:2d})  {nums}     (suma {s} · {npar}p/{K_SORTEO - npar}i · "
                  f"{nbaj} bajos/{K_SORTEO - nbaj} altos)")
        print("\n⚠  Estas combinaciones NO aumentan la probabilidad de ganar: cada boleto sigue")
        print("   teniendo 1 entre 32,468,436 de acertar. Solo evitan combinaciones atípicas.")
        print("   Los mismos 6 números sirven para Melate, Revancha y Revanchita.\n")

    # Reporte: se imprime por defecto; con -o se guarda; se omite si solo se pidieron combinaciones.
    if args.output or not args.combinaciones:
        reporte = construir_reporte(carpeta, args.desde, args.juego)
        if args.output:
            Path(args.output).write_text(reporte, encoding="utf-8")
            print(f"Reporte guardado en: {args.output}")
        else:
            print(reporte)

    if args.grafico:
        generar_grafico(carpeta, args.grafico)


if __name__ == "__main__":
    main()
