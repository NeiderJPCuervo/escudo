# Escudo

**Detección de fraude en tiempo real para pagos inmediatos.** Decide cada transferencia *antes* de que
el dinero se mueva (APPROVE, STEP_UP, REVIEW o DECLINE), con reglas explicables, un modelo portable y
análisis de redes de cuentas mula.

Contexto: en Colombia, Bre-B (el sistema de pagos inmediatos del Banco de la República) hace que las
transferencias sean gratuitas, instantáneas e irrevocables. El fraude se detiene antes o no se
detiene.

> Estado: **semana 1 de 7**. Ya existen el dominio completo, el simulador con semilla y la CI.
> La API, el *streaming*, n8n y la vitrina pública llegan en las siguientes semanas (ver *Hoja de ruta*).

## Línea base (reproducible)

```bash
uv run escudo-baseline --seed 2
```

| Política | Dinero de fraude detenido | Recall | Precisión | Bloqueos legítimos por 1 000 |
|---|---|---|---|---|
| Sin protección | 0,0 % | 0,0 % | — | 0,0 |
| Regla ingenua (monto ≥ 3 M) | 22,9 % | 3,0 % | 31,8 % | 2,4 |
| Solo reglas Escudo | 44,2 % | 35,1 % | 47,4 % | 14,3 |

Datos del día de evaluación:
- 6 526 transferencias simuladas, de las cuales 231 son fraudulentas;
- 156,4 M COP en fraude;
- incluye clientes legítimos "difíciles" (llaves nuevas, cambios de celular, viajeros, ráfagas de
  amigos) y ataques discretos.

La CI exige que estas cifras no cambien sin querer. La política "reglas + modelo" llega en la
semana 2, con el entrenamiento.

## Estructura

```text
escudo/
├── packages/
│   ├── escudo-domain/    # ventanas deslizantes, features, reglas sin eval, modelo portable,
│   │                     # umbral por costo, grafo de mulas, métricas (solo biblioteca estándar)
│   └── escudo-sim/       # simulador con semilla, escenarios de ataque, políticas de línea base, CLI
├── tests/                # pruebas transversales (portabilidad a Pyodide)
├── docs/
│   ├── adr/              # decisiones de arquitectura
│   └── propuesta.md      # documento de diseño completo
├── .github/workflows/    # CI: lint, formato, mypy --strict, pruebas en Python 3.12–3.14
├── Makefile
└── pyproject.toml        # workspace de uv + configuración de ruff, mypy, pytest y coverage
```

## Cómo correrlo

Requisito: [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
make install    # crea .venv con el workspace y las herramientas
make ci         # lint + formato + mypy --strict + pruebas con cobertura + línea base
```

## Calidad

- **`mypy --strict`** en el código y en las pruebas.
- **ruff** como linter y formateador.
- **Cobertura mínima del 90 %**; hoy está por encima del 99 %.
- **Pruebas de propiedades con Hypothesis.** La ventana deslizante y el umbral por costo se comparan
  contra cálculos de fuerza bruta, y union-find contra una búsqueda en grafo.
- **Regresión de la línea base:** la semilla 2 debe reproducir la tabla de arriba
  ([ADR 0002](docs/adr/0002-simulador-con-semilla-y-regresion.md)).
- **Portabilidad:** una prueba falla si el dominio o el simulador importan algo fuera de la biblioteca
  estándar ([ADR 0001](docs/adr/0001-dominio-solo-biblioteca-estandar.md)).

## Hoja de ruta

| Semana | Entregable |
|---|---|
| ✅ 1 | Dominio + simulador con semilla + CI |
| 2 | Entrenamiento con scikit-learn exportado a JSON · umbral por costo · política "reglas + modelo" |
| 3 | `scoring-api` (FastAPI) + Redis + PostgreSQL + idempotencia + outbox · prueba de carga |
| 4 | Redpanda + `graph-worker` (mulas) · degradación ante fallos de Redis |
| 5 | n8n: step-up por Telegram, casos para analistas, reporte diario |
| 6 | Vitrina en Netlify: el dominio corre en el navegador con Pyodide; botones de ataque en vivo |
| 7 | Re-entrenamiento con *shadow mode* y aprobación humana · video · artículo |

El diseño completo, con arquitectura, ADRs, modelo de datos y preguntas de entrevista, está en
[docs/propuesta.md](docs/propuesta.md).
