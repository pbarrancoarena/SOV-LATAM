# Knowledge Transfer - Baseline LATAM

## Resumen General

Este documento detalla el proceso de forecasting baseline (sell-out) para países de LATAM, utilizando modelos Prophet con optimización de hiperparámetros.

---

## Proceso de Forecasting

### Palancas de Control

Las **palancas principales** que se ajustan en LATAM son los **hiperparámetros del modelo Prophet**.

- Únicamente se hace **baseline** (es decir, **sell-out**)
- **No se usa la dimensión "zona"** en las combinaciones
- Se realiza forecast tanto a **nivel categoría** como a **nivel combinación**

### Estrategia de Doble Tanda

El proceso se ejecuta en **dos tandas paralelas**:

1. **Nivel Categoría**: 
   - Solo se modela **volumen** (no precio)
   - Agregación por categorías principales

2. **Nivel Combinación**: 
   - Forecast desagregado por todas las combinaciones
   - Incluye tanto **volumen** como **precio**
   - Los valores de SOV (ya con precio) usan estos forecasts desagregados

### Gestión con Stakeholders

- **Regularmente**, los stakeholders trabajan a **nivel categoría**
- Es poco común que los stakeholders entren a nivel combinación
- **Mover parámetros a nivel combinación** para cambiar un número a nivel categoría es un **esfuerzo inútil**

**Estrategia de Amadeo**: 
> Si no se logra un número esperado a nivel categoría, se usan los hiperparámetros de Prophet a nivel categoría y después se desagregan a nivel combinación.

---

## Datos y Entrenamiento

### Ventana de Datos

- **36 observaciones de Nielsen** (ventana móvil)
- Cada mes se agrega una nueva observación y se elimina la más antigua
- **Cada BAU mensual es completamente distinto** debido a esta ventana móvil
- El entrenamiento de parámetros cambia cada mes por esta razón

### Categorías

- Se analizan particularmente **7 categorías**

### Grid de Hiperparámetros

- Se crea un **grid de aproximadamente 76 combinaciones** de hiperparámetros
- Prophet es un **modelo bayesiano** donde los rangos son propuestos, no estimados

---

## Manejo de Datos Especiales

### Outliers

- **No hay ningún método de outlier detection implementado**

### Valores Negativos

- Se usa el **mecanismo de imputación de Prophet**
- **Solo aplicable a nivel combinación**
- A nivel categoría no se puede hacer esta imputación

---

## Selección de Hiperparámetros

### Métrica Principal: Mean Range Proportion

**Definición**: 
- El rango es la distancia de la predicción a los intervalos de confianza
- Esta métrica es la que Amadeo usa para escoger los hiperparámetros

### Problema del Parámetro de Tendencia

⚠️ **Hay un hiperparámetro muy sensible (tendencia)**:

- Si se ajusta mucho el parámetro de tendencia:
  - Los intervalos de confianza se hacen **muy grandes**
  - Se produce **sobreajuste**
  
- Algunas combinaciones son especialmente susceptibles a este parámetro
- Tratando de tener un `range_proportion` muy pequeño, las estimaciones resultaban malas
- **Solución**: En ocasiones se toma la **media del range proportion** como ajuste

### Evaluación de Métricas

Se definen **tres niveles de calidad** usando ciertos thresholds:

| Nivel | Comportamiento |
|-------|----------------|
| **Best** | Ocasiona **early stopping** |
| **Good** | Usa `mean_range_proportion` como criterio de desempate |
| **Acceptable** | Usa `mean_range_proportion` como criterio de desempate |

> 💡 Este criterio de desempate previene el sobreajuste y vale la pena aplicarlo especialmente a **nivel combinación**.

---

## Validación (Actualmente No Usada)

El notebook incluye una **parte de validación** que:
- **Actualmente no se usa**
- Amadeo la dejó implementada **por si se requiere en el futuro**

---

## Riesgos y Oportunidades de Mejora

### 1. 🚨 No es Automatizable

**Problema**:
- Ventana de solo **36 observaciones**
- Modelo **bayesiano** con complejidad inherente
- **Necesita mucho feedback de negocio** → **Human in the loop** obligatorio

**Impacto**: El proceso requiere supervisión y ajustes manuales constantes

### 2. 📚 Complejidad de Transferencia de Conocimiento

**Problema**:
- El proceso es **complejo de entender**
- El nuevo owner **no tiene experiencia** con el proceso
- Falta claridad sobre **por qué se cambia cada uno de los hiperparámetros**

**Impacto**: Alta dependencia del conocimiento de expertos, riesgo de continuidad

### 3. 🔮 Incertidumbre sobre Stakeholders Futuros

**Situación actual**:
- Hay una **buena relación** con los stakeholders actuales
- El proceso está calibrado a sus necesidades y conocimientos

**Riesgo**:
- **No tenemos noción** de quiénes serán los **futuros stakeholders**
- No sabemos si los **futuros operadores** tendrán:
  - El mismo nivel de conocimiento técnico
  - Las mismas expectativas del modelo
  - La misma disposición para el proceso iterativo actual

**Impacto**: Posible desalineación con requerimientos futuros

---

## Recomendaciones

1. **Documentar decisiones**: Crear un log de decisiones sobre cambios de hiperparámetros
2. **Automatización parcial**: Explorar oportunidades para automatizar pre-validaciones
3. **Capacitación**: Desarrollar material de capacitación detallado para nuevos operators
4. **Flexibilidad**: Diseñar el proceso pensando en diferentes perfiles de stakeholders
5. **Versionado**: Mantener registro histórico de configuraciones exitosas por país/categoría

---

## Referencias Técnicas

- **Modelo**: Prophet (Facebook/Meta)
- **Tipo**: Modelo Bayesiano de Series de Tiempo
- **Ventana**: 36 observaciones móviles
- **Grid Search**: ~76 combinaciones de hiperparámetros
- **Países**: Guatemala, Perú, Ecuador, Chile, Chile W/ Blues, Brasil, Argentina
- **Categorías**: 7 principales
