# BAU KO MX

## ¿Qué es BAU?

**BAU** = Business As Usual

Es un proyecto heredado de otro vendor (OPI comprado por Kavak).
Tiene un preprocesamiento y luego otro que solo es para forecasting. Ya no se hace el preprocesamiento. 

## Forecasting Process

1. **data_prep_price**: outlier detection
2. **Forecasts**: prices and unit cases (KO | NOKO)
3. **Escenario target**

## Variables de Dimensión

`Bottler` `Zona` `Canal` `Categoria` `Subcategoria` `Segmento` `Empaque` `Retornabilidad`

## Definiciones

- **SOM** = Ventas KO / ventas de la Industria
- **SOV** = Revenue KO / revenue Industria

## Notas Importantes

- Cuando hablan de Share casi siempre es **Share of Value**
- Error de BAU de México debe ser **menor a 0.05**
- De todos los forecast salen **tres forecast**: el lower, el upper y el normal
- A nivel nacional sale mejor el original. A nivel categoría sale mejor el que es a nivel categoría

## Proceso Detallado

### 1. Preprocesamiento

- Elimina precios negativos
- Elimina outliers por combinación y por año
  - Se imputan conforme a la media
  - Se imputan con forward o backward para discontinuidades largas

### 2. Limpieza de outliers

- 850 combinaciones a 7 niveles
- Son 36 meses agrupadas por año
- Tomamos mínimo, máximo y mediana. La mediana por 3
- Se junta con la combinación. Se checa que esté entre 3 veces la mediana o el mínimo
- Si está fuera de ese rango se cambia por la mediana
- **Nota**: *Sospechoso que algo sea menor al mínimo*

### 3. Forecast de precios

- Para KO, es importante hacer un **chequeo visual de la serie**, para las que tengan comportamiento especial que son dos
- Cambiar menores a cero por cero
- Si hay missings se imputan
- El horizonte a pronosticar es **Year To GO**
- Para `HoltWinter`, `ExponentialSmoothing`
- **Reporte de Strategy**: Ahí viene el error que usan Métrica de Error

### 4. Forecast de Unit Cases

- Se usa `Prophet` con crecimiento logístico
- **Holiday** - Boycot
- **Cap y floor** (máximo esperado y mínimo esperado)
- Se le da ciertos hiperparámetros

### 5. Consolidate

- Se juntan los pronósticos

### 6. Target Escenario

- **NO-KO** upper de baseline
- **KO** se corre el modelo con el (Con NSR sell in, queremos predecir el sell out Nielsen)

|                 | **X**      | **Y**      |
| --------------- | ---------------- | ---------------- |
| **Train** | NSR Sell In      | Nielsen Sell Out |
| **Test**  | Rolling Estimate | y_hat target     |

## Ruta del Entregable

```
KO México → 4 OS → 02 Market Insights → Reporte Strategy → 2025 → (Excel - PPT)
```

## Referencias

- [Wiki - Data Science Forecast](https://wiki.coke.com/confluence/spaces/LAGRDC/pages/235951497/Data+Science+-+Forecast)
