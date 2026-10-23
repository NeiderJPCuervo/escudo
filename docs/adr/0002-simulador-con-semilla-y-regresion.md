# ADR 0002: Simulador con semilla y regresión de la línea base

- Estado: aceptado
- Fecha: 2026-10-23

## Contexto
No hay datos reales de fraude (y no deben usarse). Para comparar políticas hace falta un mundo
simulado con *ground truth*.

La prueba de concepto mostró un riesgo: la primera versión del simulador daba **100 % de detección**
porque era demasiado fácil. Un número así destruye la credibilidad del proyecto en una entrevista.

## Decisión
- El simulador (`escudo-sim`) es **determinista por semilla**. Un día 0 sirve de historia de
  calentamiento y el día 1 se evalúa con ataques.
- Incluye **legítimos difíciles**:
  - llaves nuevas;
  - cambios de celular;
  - viajeros;
  - compras grandes;
  - amigos que dividen una cuenta en ráfaga.
- Incluye **fraudes difíciles**:
  - atacantes con montos discretos;
  - mulas con llaves antiguas;
  - víctimas de estafa que confirman el step-up.
- Cada escenario de ataque es un método independiente, para que la vitrina pueda dispararlos por
  separado.
- El **orden de las llamadas al generador aleatorio es parte del contrato**.
  `packages/escudo-sim/tests/test_baselines.py` exige que la semilla 2 reproduzca la tabla publicada
  en la propuesta (dinero detenido: 0 %, 22,9 % y 44,2 %; recall, precisión y bloqueos legítimos
  por cada 1 000).
- La CI corre en Python 3.12, 3.13 y 3.14, y verifica que el resultado no dependa de la versión.

## Consecuencias
- **Positivas:**
  - Cualquier cambio que altere las cifras se detecta en la CI.
  - La refactorización del simulador en métodos por escenario se validó con esa prueba sin cambiar
    un solo número.
- **Negativas:** cambiar el simulador a propósito obliga a actualizar la prueba y la propuesta en el
  mismo commit. Es intencional: las cifras publicadas y el código no pueden divergir.
- **Límite que hay que decir en voz alta:** son números de un simulador diseñado por nosotros, no un
  *benchmark* del mundo real. Sirven para comparar políticas en igualdad de condiciones.
