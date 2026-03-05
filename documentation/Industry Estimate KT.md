# Industry Estimate KT - Knowledge Transfer

## Objetivo del Proyecto
Pronosticar el sell-in de KO y de competidores (NO KO) mediante aproximaciones estadísticas.

## Clasificación de Países
- **Países Nielsen**: 7 países donde contamos con información del sell-in
- **Países No Nielsen**: Colombia y Bolivia

## Modelos de Pronóstico

### 1. Baseline (Modelo Base)
Modelo fundamental que sirve como línea base para las predicciones.

### 2. Precision Plus
Agrega componente de variables exógenas para mejorar la precisión del pronóstico.

### 3. Modelo Target
Rolling Estimate que funciona como meta u objetivo de ventas.

## Ventanas de Tiempo

- **Corto Plazo**: Hasta que termine el siguiente año (meses)
- **Mediano Plazo**: Próximo año (meses)  
- **Largo Plazo**: Tres años siguientes

**Nota**: Se pronostica tanto el **Volumen** como el **Precio**. El precio tiende a ser estable, mientras que el volumen es más complejo de predecir.

El pronóstico se realiza a diferentes niveles de granularidad para distintas categorías, variables y embotelladores.

## Clasificación de Categorías

### Categorías Conocidas
- Contamos con información de sell-in (NSR) y sell-out (Nielsen)
- Mayor precisión en los pronósticos

### Categorías Semiconocidas  
- No hay información de sell-out disponible
- Solo datos de sell-in

### Categorías No Conocidas
- No tenemos ni sell-in ni sell-out
- Solo hay información de competidores (NO KO)

## Metodologías Detalladas

### Baseline

#### SM Forecast Partial
**Frecuencia**: Mensual o bajo demanda  
**Duración**: Aproximadamente 3 horas de procesamiento

##### Categorías Conocidas (Corto y Mediano Plazo)
- Alineación del pronóstico para que el sell-in sea similar al sell-out
- Modificaciones posteriores por parte del equipo de negocio para alinear expectativas del cliente

##### Categorías Semiconocidas (Corto y Mediano Plazo)
- Basado únicamente en sell-in (NSR de tres años)
- Utiliza Prophet con parámetros por defecto

##### Categorías No Conocidas (Corto y Mediano Plazo)
- Estimación de ventas mediante regresión lineal
- Distribución proporcional por embotellador
- Granularidad: nivel mensual por bottler

#### Industry Outlook (Largo Plazo)
- Enfoque en tendencias más que en niveles mensuales
- Regresión lineal usando año como variable X y volumen como variable Y
- Mayor peso a observaciones más recientes
- Aplicación de ponderaciones específicas

### Precision Plus

#### Pronóstico con Variables Exógenas (Corto y Mediano Plazo)
- Incorpora variables climáticas y económicas proporcionadas por KO
- Utiliza cinco variables exógenas principales
- Enfoque en sell-in únicamente
- **Criterios de selección de variables**:
  - Correlación superior a 0.4
  - Sentido de negocio lógico
- Proceso: análisis a nivel industria → análisis separado → distribución basada en análisis separado

#### Precision Plus Outlook (Largo Plazo)
- Dos modelos iterativos
- Filtro de variables por correlación y coeficientes (~100 variables)
- Análisis por bottler y categoría

**Modelo de Coeficientes**:
- Evaluación de coeficientes de regresión lineal
- Eliminación de variables sin sentido de negocio
- Filtrado por p-value alto
- Proceso iterativo de refinamiento
- Metodología: industria → separado → distribución

### Modelo Market Dynamics Target

#### Concepto Base
KO mantiene pronósticos/planes de venta para los próximos años. El objetivo es determinar las ventas de competidores si KO alcanza sus metas.

#### Metodología
- Análisis de comportamientos anuales 2010-2024
- Regresiones lineales por categoría
- Determinación de crecimiento de NO-KO basado en crecimiento de KO
- Identificación de relaciones: complementarias vs. competitivas

#### Target Regression
Estimación de crecimiento anual de NO-KO basada en el crecimiento target de KO.

#### Target Prophet
- Variable exógena: KO
- Implementación de PCA
- Uso de Prophet como algoritmo base

## Output Final
El resultado del análisis de ciencia de datos se presenta en formato de layout estructurado para consumo del negocio.

---

## Próximos Pasos y Consideraciones
- Validación continua de modelos
- Monitoreo de precisión de pronósticos
- Ajustes estacionales según sea necesario
- Incorporación de nuevas variables exógenas relevantes