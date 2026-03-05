---
marp: false
theme: default
paginate: true
---
# Semi Automatización del Forecasting QA con agentes y Prompt Engineering

### Draft de propuesta

<!-- load logo arena_analytics_renewed_new-13.png-->

![Logo](images/logo_arena_analytics_renewed_new-13.png)


---

# Contexto

Trabajar con series de tiempo siempre trae retos:
modelos que no generalizan bien, parámetros difíciles de ajustar, y procesos manuales que no escalan.

En nuestro caso:

- Prophet presenta problemas de ajuste a nivel combinación en algunas ocasiones.
- Esto genera imprecisiones en el cálculo del SOV.
- El proceso actual requiere ajustar manualmente **82 combinaciones × 8 países** cada mes.
- Este flujo no es eficiente ni sostenible.

---
# Consideraciones 

- Antes de implementar cualquier solución, es crucial preguntarnos:
  - La solución debe ser escalable y sostenible. ¿Usar LLMs es necesario o puedo resolverlo de una manera más simple?
  - ¿Cual seria el impacto de llevar esta solución a producción? ¿Cómo afectaría esto a los procesos actuales y al equipo?
  - ¿Cual seria el valor agregado? ¿Mejoraría significativamente la precisión del forecast o la eficiencia del proceso?
---

[![](https://mermaid.ink/img/pako:eNptlF9P2zAUxb-KdR8m0BpGkzZtIoZW-kc8rGIP1SYN8-A6t4m1xK4cByil3303CaW04iXSPfd37OsTJ1uQJkGIwfM8rqXRK5XGXDOWi42pXMwSkVrkummvcvMkM2EdW9zUDGOjew4zY1GK0rGfo8VozuGBeR5bWCwzkyfsSVitdFqSeM1uzjgsrErRslGK2pUcztuFbpr-eMvhlzVJJV0LcNixL0x37xt9naFj0-c1Wmo8tMZxvdudxsY_IW6iVmhRS2RnX5l3fgwunkwDTglcqALZzAp6nhnpXrV5fE2UPHVkFtvFZ-S5W5ZoHzFhc1WWhXAye6d19-Mk2if6dkOjrkW9hUNbnqD7WXRA6PQZZeVonrcwT9n3KXSP6D_WEEtJ5EILp4x-xyct1Cfot8hVctydvnXbanZUaf-4DI7L3nHZb8uQ9pkjvZWRlLgWdepjq-iwShxOELbs4MeWbtUS85hxuCqJZqXb5Pidcw5LIf-l1lQ68aTJjY1r8fq2Kog6HOTqW2275sB2XL_dQFq1zMQa6aoud_vMPohKFHvZP8iUstvLwedy73O5_7k8OJGhA6lVCcTOVtiBAm0h6hK2tYGDy7BADnUWCa5EldMr57q20Qn_GlPsnRRKmu2Lak1B4ETRRykOBOoE7ZjCcxBHzQIQb-EZYr97eTEc9LoD3w_DKOxdDjuwITm68IdhEHW7fj-Iwijwdx14afa8vCAu8sN-QK7-cOCTAxPljJ23_4nmd7H7DwIBRn0?type=png)](https://mermaid.live/edit#pako:eNptlF9P2zAUxb-KdR8m0BpGkzZtIoZW-kc8rGIP1SYN8-A6t4m1xK4cByil3303CaW04iXSPfd37OsTJ1uQJkGIwfM8rqXRK5XGXDOWi42pXMwSkVrkummvcvMkM2EdW9zUDGOjew4zY1GK0rGfo8VozuGBeR5bWCwzkyfsSVitdFqSeM1uzjgsrErRslGK2pUcztuFbpr-eMvhlzVJJV0LcNixL0x37xt9naFj0-c1Wmo8tMZxvdudxsY_IW6iVmhRS2RnX5l3fgwunkwDTglcqALZzAp6nhnpXrV5fE2UPHVkFtvFZ-S5W5ZoHzFhc1WWhXAye6d19-Mk2if6dkOjrkW9hUNbnqD7WXRA6PQZZeVonrcwT9n3KXSP6D_WEEtJ5EILp4x-xyct1Cfot8hVctydvnXbanZUaf-4DI7L3nHZb8uQ9pkjvZWRlLgWdepjq-iwShxOELbs4MeWbtUS85hxuCqJZqXb5Pidcw5LIf-l1lQ68aTJjY1r8fq2Kog6HOTqW2275sB2XL_dQFq1zMQa6aoud_vMPohKFHvZP8iUstvLwedy73O5_7k8OJGhA6lVCcTOVtiBAm0h6hK2tYGDy7BADnUWCa5EldMr57q20Qn_GlPsnRRKmu2Lak1B4ETRRykOBOoE7ZjCcxBHzQIQb-EZYr97eTEc9LoD3w_DKOxdDjuwITm68IdhEHW7fj-Iwijwdx14afa8vCAu8sN-QK7-cOCTAxPljJ23_4nmd7H7DwIBRn0)

---

# Propuesta de Solución (1)

## Agentes para Automatizar Reentrenamientos

Implementar un sistema de *agentes* que monitorice cada combinación y decida cuándo reentrenar.

Los agentes ejecutarían:

### 1. Detección de patrones anómalos

Identificación automática de disparidades en el forecast o métricas que superan umbrales predefinidos.
¿Antes que implementar un agente? Esto se puede lograr mediante una automatización basada en reglas o modelos estadísticos simples. 

---

# Propuesta de Solución (1)

### 2. Evaluación bajo criterios de negocio

Reglas inspiradas en prácticas de producto:

- estabilidad de tendencia
- cambios abruptos
- interpretabilidad del comportamiento

---

# Propuesta de Solución (1)

### 3. Reentrenamiento automatizado

Aplicación de prompts estructurados que optimicen:

- cambio en los hiperparámetros
- configuración de estacionalidades
- control de changepoints
- criterios de validación

---

# Marco de Diseño

## Agentes Especializados

Un posible diseño:

### • Atuomatizacion de disparidades

Evalúa desviaciones, detectar disparidades en forecasts. Y disparar alertas.

### • Agente de Decisión

Interpreta reglas de producto + métricas estadísticas.
Define si es necesario reentrenar. Y con qué enfoque.

---

# Marco de Diseño

### • Agente de Reentrenamiento

Ejecuta prompts técnicos (tuning de Prophet, evaluación, cross-validation).
Genera código reproducible para el pipeline.

### • Agente de Reporte

Da trazabilidad: qué se ajustó, por qué y con qué impacto.

---

## • Validación Humana o Revision por agente
Loop de feedback para supervisar decisiones críticas.
Delimitar criterios de aceptación automática vs revisión humana.

---

# Propuesta de Solución (2)

## Interfaz Human-in-the-Loop

Aunque el sistema se automatiza, se mantiene supervisión humana mediante un visor desarrollado con:

- **Stremio + Chart** (o stack equivalente)
- Panel con:
  - combinaciones,
  - hiperparámetros explorados,
  - resultados del reentrenamiento,
  - comparación visual entre forecasts.

---

# Propuesta de Solución (2)

## Interfaz Human-in-the-Loop

Esto permite seleccionar fácilmente parámetros que mejor simulan la serie, validando comportamientos antes de moverlos a producción.

---

# Ejemplos de Prompts Adaptados a la Solución

### Prompt para Reentrenamiento Automático con Prophet

```
Como experto en Prophet, evalúa si este modelo requiere reentrenamiento.
Analiza:

* tendencia actual,
* estacionalidades,
* residuales,
* desviación frente al último forecast,
* métricas: MAPE, MAE, estabilidad.

Si el modelo está degradado, genera:

* una recomendación técnica,
* parámetros ajustados,
* código reproducible para reentrenar,
* breve justificación estadística.
```

---

### Prompt para Evaluación del Agent de Monitoreo

```
Analiza esta serie y su forecast actual.
Identifica patrones inconsistentes:

* rupturas de tendencia
* crecimiento o caída anormal
*puntos de cambio no explicados
* pérdida de estacionalidad.

Devuelve:

* diagnóstico
* indicador de disparidad
* recomendación para el agente de decisión.
```

Aqui podriamos trabajar con Producto para elaborar una serie de prompts dependiendo de las reglas que consideren más relevantes.

---

### Prompt para Explorar Hiperparámetros

```
Dado este histórico y estos hiperparámetros de Prophet, genera:

* ariantes basadas en escala logarítmica,
* fectos esperados,
* ombinaciones óptimas para estabilidad,
* ustificación estadística.
```

Aqui podriamos elaborar del lado de ciencia una serie de prompts técnicos para explorar diferentes hiperparámetros de Prophet. Pidiendo al LLM que proporcione un JSON con las combinaciones a probar y una breve justificación estadística.

---

# Flujo Completo Propuesto

1. Monitoreo automático por combinación.
2. Detección de patrones anómalos.
3. Evaluación contra reglas de producto.
4. Reentrenamiento con prompts estructurados.
5. Registro y explicación de acciones.
6. Validación humana mediante visor interactivo.
7. Actualización del forecast final.


---
