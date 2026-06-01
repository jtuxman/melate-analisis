# Reporte de análisis — Melate, Revancha y Revanchita

- **Fecha del reporte:** 31/05/2026
- **Fuente:** `Melate.csv`, `Revancha.csv`, `Revanchita.csv` (histórico oficial de sorteos)
- **Cobertura:** hasta el concurso **4219 (29/05/2026)**
- **Alcance:** análisis estadístico exploratorio (frecuencias, patrones combinatorios y evolución de la bolsa)

> ⚠️ **Nota previa.** Este es un análisis descriptivo con fines educativos. La lotería es un juego de azar: como se demuestra más abajo, **ningún hallazgo aquí permite predecir resultados ni mejora la probabilidad de ganar**. Cada combinación es y seguirá siendo equiprobable.

---

## Resumen ejecutivo

1. **Los sorteos son estadísticamente justos.** En el periodo de formato estable (2007+), el test χ² de uniformidad confirma que no existen números "calientes" ni "fríos" reales en ninguno de los tres juegos.
2. **El formato del Melate cambió 5 veces** (de 1–39 en 1984 a 1–56 desde 2007). Esto invalida cualquier análisis de frecuencias sobre el histórico completo; hay que filtrar a **2007 en adelante**.
3. **Existen patrones combinatorios reales** (pares/impares, bajos/altos, suma ≈ 170), pero son consecuencia matemática de elegir 6 de 56, no un sesgo del sorteo, y no dan ventaja para ganar.
4. **La bolsa sí cuenta una historia:** crecimiento sostenido desde 2007, récord real de **\$639.5 M (julio 2013)** y un acumulado histórico de **157 sorteos sin ganador** entre 2021 y 2022.

---

## 1. Datos analizados

| Archivo | Juego | NPRODUCTO | Sorteos | Concursos | Desde | Columnas de números |
|---|---|---|---|---|---|---|
| `Melate.csv` | Melate | 40 | 4,219 | 1 → 4219 | 19/08/1984 | R1–R6 + **R7** (adicional) |
| `Revancha.csv` | Revancha | 41 | 3,211 | 1009 → 4219 | 06/08/1997 | R1–R6 |
| `Revanchita.csv` | Revanchita | 34 | 1,849 | 2371 → 4219 | 25/08/2010 | F1–F6 |

**Estructura de columnas:** `NPRODUCTO, CONCURSO, [números], BOLSA, FECHA` (fecha en formato `dd/mm/aaaa`).

Revancha y Revanchita son sorteos derivados añadidos después; por eso arrancan más tarde y **comparten el número de concurso con Melate**.

---

## 2. Calidad de los datos

| Verificación | Melate | Revancha | Revanchita |
|---|---|---|---|
| Valores nulos | 0 | 0 | 0 |
| Concursos duplicados | 0 | 0 | 0 |

Los datos están limpios. Las dos únicas salvedades —cambio de formato y manejo de la bolsa— se documentan en las secciones 3 y 6.

---

## 3. Hallazgo crítico: el formato cambió 5 veces

El rango de números sorteados **no es constante** en el histórico. El número máximo sorteado por época revela el formato vigente:

| Periodo | Rango de números |
|---|---|
| 1984–1992 | 1–39 |
| 1993–2001 | 1–44 |
| 2002–2004 | 1–47 |
| 2005 | 1–50 |
| 2006 | 1–51 |
| **2007–hoy** | **1–56** (estable) |

**Implicación:** un análisis de frecuencias sobre todo el histórico es engañoso. Los números altos (51–56) parecen "fríos" únicamente porque **no existían antes de 2006–2007**, no por ningún sesgo. Por eso **todo el análisis de frecuencias se restringe a 2007+**. Revanchita ya nace en formato 1–56 (2010).

---

## 4. Análisis de frecuencias (formato estable 2007+)

### 4.1 Los sorteos son justos (test χ²)

Con 56 números y una frecuencia esperada por número de ~239 (Melate/Revancha) o ~198 (Revanchita), el test de uniformidad da:

| Juego | Sorteos | χ² observado | Crítico (5%, gl=55) | Veredicto |
|---|---|---|---|---|
| Melate | 2,229 | 50.5 | ≈ 73.3 | ✅ Compatible con azar |
| Revancha | 2,229 | 43.2 | ≈ 73.3 | ✅ Compatible con azar |
| Revanchita | 1,849 | 47.6 | ≈ 73.3 | ✅ Compatible con azar |

En los tres casos el χ² queda **muy por debajo** del valor crítico → **no hay sesgo detectable**.

### 4.2 Números "calientes" y "fríos" (son ruido del azar)

Las desviaciones de ±14 % respecto a lo esperado son exactamente las que produce un bombo justo. **No tienen poder predictivo.**

| Juego | Más frecuentes (desv. %) | Menos frecuentes (desv. %) |
|---|---|---|
| **Melate** | 29 (+14%), 19 (+13%), 50 (+11%), 5 (+9%), 21 (+8%) | 37 (−14%), 34 (−12%), 27 (−11%), 53 (−10%), 23 (−10%) |
| **Revancha** | 24 (+12%), 4 (+10%), 5 (+9%), 50 (+9%), 26 (+8%) | 11 (−12%), 42 (−10%), 52 (−10%), 10 (−8%), 20 (−8%) |
| **Revanchita** | 54 (+13%), 10 (+12%), 40 (+12%), 24 (+9%), 49 (+9%) | 23 (−13%), 18 (−13%), 51 (−12%), 39 (−12%), 37 (−11%) |

### 4.3 Mayor atraso (sorteos sin aparecer, al 29/05/2026)

Dato frecuentemente solicitado, aunque tampoco predice nada (falacia del jugador):

- **Melate:** 43 y 31 (35 sorteos sin salir), 1 (30), 23 (29).
- **Revancha:** 10 (43 sorteos), 28 (30), 37 (27).
- **Revanchita:** 2 (27 sorteos), 15 (23), 11 (22).

> El número adicional **R7** de Melate sale del mismo bombo, por lo que su distribución es igualmente uniforme.

---

## 5. Patrones combinatorios reales (no son sesgo del bombo)

Estos patrones **sí son reales y consistentes en los tres juegos**, porque derivan de la combinatoria de elegir 6 de 56 —no de un defecto del sorteo—. Describen cómo se ve una combinación "típica", pero **no aumentan la probabilidad de ganar**.

### 5.1 Pares / impares (de los 6 números)

| Composición | Frecuencia aprox. |
|---|---|
| 3 pares / 3 impares | **~34 %** (lo más común) |
| 2–4 o 4–2 | ~23 % cada una |
| 1–5 o 5–1 | ~8 % cada una |
| 0–6 o 6–0 (todos iguales) | ~1–2 % cada una |

### 5.2 Bajos (1–28) vs altos (29–56)

Media de **3 bajos / 3 altos** en los tres juegos. El reparto mitad y mitad domina.

### 5.3 Suma de los 6 números

| Juego | Media | Mediana | Rango histórico | 80 % central |
|---|---|---|---|---|
| Melate | 170 | 169 | 58 – 286 | ~122 – 219 |
| Revancha | 171 | 170 | 55 – 297 | ~123 – 218 |
| Revanchita | 172 | 174 | 60 – 275 | ~122 – 220 |

> **Combinación "representativa" del histórico:** 3 pares / 3 impares, 3 bajos / 3 altos y suma ≈ 170. Útil únicamente para **evitar combinaciones que casi nadie juega** (y así no compartir un eventual premio), nunca para aumentar la probabilidad de ganarlo.

---

## 6. Análisis de la bolsa (el dinero)

### 6.1 Dos correcciones obligatorias

1. **Reconversión monetaria de 1993** (México quitó 3 ceros al peso). En los datos el salto es exacto entre el concurso **528** (\$3,500 M pesos viejos, 27/12/1992) y el **529** (\$1 M pesos nuevos, 30/12/1992). Para comparar en pesos de hoy: dividir entre 1000 los concursos **≤ 528**.
2. **`BOLSA = 0` es dato faltante**, no una bolsa real (173 casos dispersos entre los concursos 1 y 2234, hasta 03/05/2009). Se tratan como nulos. La serie es continua desde el concurso **2235** (06/05/2009).

### 6.2 Récord real (corregido)

| Posición | Concurso | Fecha | Bolsa (pesos de hoy) |
|---|---|---|---|
| 🥇 | 2677 | 31/07/2013 | **\$639.5 millones** |
| 🥈 | 2676 | 28/07/2013 | \$632.5 millones |
| 🥉 | 2675 | 24/07/2013 | \$627.0 millones |

> El "récord" aparente de **\$12,000 millones (1992)** es un espejismo: en pesos de hoy equivale a solo **\$12 millones**.

### 6.3 Evolución de la bolsa promedio por periodo

| Periodo | Promedio | Máximo |
|---|---|---|
| 1985–1989 | \$1 M | \$2 M |
| 1990–1994 | \$3 M | \$60 M |
| 1995–1999 | \$10 M | \$50 M |
| 2000–2004 | \$19 M | \$94 M |
| 2005–2009 | \$61 M | \$406 M |
| **2010–2014** | **\$147 M** | **\$640 M** |
| 2015–2019 | \$128 M | \$546 M |
| 2020–2024 | \$139 M | \$505 M |
| 2025–2029 (parcial) | \$104 M | \$272 M |

El salto grande ocurre **a partir de 2005–2010**. No es inflación (todo está en pesos nuevos): coincide con el cambio de formato a 1–56 en 2007, que hace más difícil acertar y, por tanto, la bolsa se acumula más alto.

### 6.4 Dinámica de acumulación (periodo continuo 2009+, 1,985 sorteos)

- **Probabilidad de acertar 6 de 56:** 1 en **32,468,436**.
- El premio mayor **se reparte en promedio cada ~41 sorteos** (≈ 3–4 meses).
- Cada racha de acumulación dura **~40 sorteos de media**.
- **Racha histórica:** **157 sorteos consecutivos sin ganador**, entre **dic/2021 y dic/2022**, llevando la bolsa de \$30 M hasta **\$505 M** antes de caer.

### 6.5 Estado actual

Al último sorteo del archivo (**#4219, 29/05/2026**), la bolsa de Melate está en **\$30.1 millones** — un valor de "piso", lo que indica que hubo un ganador reciente y el acumulado venía de reiniciarse.

---

## 7. Conclusiones

1. **Los números no tienen memoria ni sesgo.** El análisis estadístico riguroso (χ²) confirma que los tres sorteos son justos. Las estrategias basadas en números "calientes", "fríos" o "atrasados" no tienen fundamento.
2. **Los únicos patrones reales son combinatorios** (pares/impares, bajos/altos, suma) y no ofrecen ventaja para ganar, solo para no compartir premio.
3. **La bolsa es la dimensión con narrativa propia:** crecimiento estructural desde 2007, récord real de \$639.5 M en 2013 y acumulados que pueden extenderse más de un año.

---

## Notas metodológicas

- Frecuencias y patrones calculados sobre los **6 números principales** de cada juego (en Melate, R1–R6; el adicional R7 se analiza por separado).
- Análisis de frecuencias restringido a **FECHA ≥ 2007-01-01** (formato 1–56 estable).
- Montos de la bolsa **normalizados a pesos nuevos** (concursos ≤ 528 divididos entre 1000); `BOLSA = 0` excluido como dato faltante.
- Detección de reinicio de bolsa: una caída **> 15 %** respecto al sorteo anterior se interpreta como reparto del premio mayor.
- Herramientas: Python 3 + pandas.

*Reporte generado el 31/05/2026 a partir del histórico de sorteos disponible en el directorio del proyecto.*
