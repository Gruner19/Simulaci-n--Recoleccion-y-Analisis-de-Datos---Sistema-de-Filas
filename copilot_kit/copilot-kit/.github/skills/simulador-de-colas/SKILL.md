---
name: simulador-de-colas
description: Reglas para implementar, verificar y ejecutar el simulador de colas M/M/c y M/D/c con SimPy (semillas independientes, calentamiento, fórmulas teóricas de verificación). Úsalo al tocar código de simulación, semillas, plan de corridas o verificación contra la teoría.
---
# Simulador de colas M/M/c y M/D/c

## Modelo
Llegadas de Poisson (tasa λ), c servidores idénticos, una fila FIFO infinita, servicio de media 1 min (μ = 1),
exponencial ("exp") o constante ("const"). Respuesta por corrida: espera media en cola de los clientes posteriores
a los primeros W (calentamiento). El código validado está en `referencia/simulador.py`; reutilízalo.

## Semillas y reproducibilidad
- Una `np.random.Generator` por corrida, creada desde un hijo de `SeedSequence(semilla_mestra).spawn(n)`.
- Genera antes de simular los vectores de tiempos entre llegadas y de servicio: la corrida queda determinada por su semilla.
- Nunca uses `np.random.seed`, semillas consecutivas ni un mismo generador compartido entre corridas.
- El resultado no debe depender del número de procesos ni del orden en que terminan las tareas.
- La semilla del orden de ejecución (permutación uniforme) es distinta de la de las corridas y de la del piloto.

## Verificación teórica (utilización ρ = λ/(cμ) < 1)
- M/G/1 (Pollaczek–Khinchine): Wq = ρ(1 + cs²) / (2μ(1 − ρ)), con cs² = 1 (exp) o 0 (const).
- M/M/c (Erlang C): a = λ/μ; C = [a^c / (c!(1−ρ))] / [Σ_{k<c} a^k/k! + a^c / (c!(1−ρ))]; Wq = C / (cμ − λ).
- M/D/c con c > 1 NO tiene fórmula cerrada simple: indícalo en la interfaz y no lo marques como verificado.
- Verifica con corridas LARGAS (p. ej. 400.000 clientes, 5 réplicas). Referencia: error máximo ≈ 1,3 %; criterio de aceptación < 2 %.

## Calentamiento y tamaño de corrida
- Sistema inicial vacío ⇒ transiente. Usa el procedimiento de Welch (media entre réplicas por índice de cliente,
  media móvil) para revisar W. Con ρ = 0,9 los primeros 500 clientes esperan ≈ 17 % menos que el régimen estacionario.
- Valores por defecto: N = 50.000, W = 1.000. Cada corrida cuesta ≈ 0,45 s (orientativo).

## Errores típicos
- Tratar los clientes de una corrida como muestra independiente (ACF ≈ 0,99 en lag 1).
- Llamar "réplicas" a lotes de una corrida larga.
- Olvidar validar ρ < 1 en todas las celdas antes de ejecutar.
