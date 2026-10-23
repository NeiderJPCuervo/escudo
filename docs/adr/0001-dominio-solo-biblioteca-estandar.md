# ADR 0001: El dominio y el simulador usan solo la biblioteca estándar

- Estado: aceptado
- Fecha: 2026-10-23

## Contexto
Escudo se muestra de dos formas:
- **Vitrina pública gratuita en Netlify.** El plan Free no ejecuta Python en sus funciones, así que
  el motor tiene que correr en el navegador del entrevistador con Pyodide.
- **Sistema completo.** FastAPI, Redis, Redpanda y n8n.

Queremos que **el mismo código** decida en ambos lados: si hay dos implementaciones, divergen.

## Opciones consideradas
1. **Dominio con numpy/scikit-learn.**
   - A favor: modelos más potentes.
   - En contra: Pyodide tarda más en cargar; servir árboles exige dependencias pesadas.
2. **Reimplementar el motor en TypeScript para la vitrina.**
   - En contra: dos fuentes de verdad, y la demo dejaría de probar el código real.
3. **Dominio y simulador en Python puro de la biblioteca estándar.**
   - A favor: el modelo se entrena fuera (scikit-learn) y se sirve desde JSON.

## Decisión
Opción 3. `escudo-domain` y `escudo-sim` no tienen dependencias externas.
`tests/test_portability.py` lo verifica en cada ejecución de la CI analizando los `import` de cada
módulo. También verifica que el dominio no dependa del simulador.

## Consecuencias
- **Positivas:**
  - La vitrina ejecuta exactamente el código probado.
  - El dominio arranca en milisegundos y se prueba sin infraestructura.
- **Negativas:**
  - El modelo de producción v1 es lineal (logístico) y se sirve en Python puro.
  - Un modelo de árboles (GBM) queda como extensión y deberá demostrar con métricas que compensa
    perder la portabilidad.
- **Si la decisión resulta equivocada:** la frontera ya existe (`LogisticModel.score`), así que se
  puede añadir otro adaptador de modelo solo para el modo completo.
