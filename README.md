# App Costeador Agroindustrial

Esta aplicación fue desarrollada en respuesta al requerimiento de construir un sistema de costeo avanzado para la manufactura agroindustrial (deshidratación y molienda).

## Stack Tecnológico
* **Frontend:** Streamlit, Pandas y Plotly (para gráficas).
* **Backend / Base de Datos:** Firebase Firestore (se ha implementado un mock local para correr la app sin credenciales reales para su prueba).

## Reglas de Negocio Implementadas
1. **Moneda Base:** Todos los cálculos se realizan e indican en Bolivianos (Bs.).
2. **Fórmula de Rentabilidad:** Se utilizó estrictamente la fórmula de *Margen sobre el Precio* (`Precio = Costo / (1 - Margen)`).
3. **Nomenclatura:** Se respetaron los nombres "Margen Fika", "Margen PDV" y "Impuestos".
4. **Estructura de Costos:**
   - **MPD (Materia Prima Directa):** Contempla la merma generada durante procesos de deshidratación.
   - **Empaque:** Módulo independiente para controlar insumos físicos.
   - **MOD (Mano de Obra Directa):** Calculada en base a horas totales por el costo hora.
   - **CIF (Costos Indirectos de Fabricación):** Modulo que suma costos como energía o depreciación.
5. **Persistencia de Datos:** Sistema de guardado y carga simulando la persistencia a Firestore.
6. **Manejo de errores:** Evita el error de división por cero comprobando que los márgenes introducidos nunca sean superiores o iguales al 100%.

## Instalación y Ejecución

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecuta la aplicación de Streamlit:
```bash
streamlit run app.py
```

*Nota: La aplicación correrá con una base de datos en modo "mock" usando un archivo local JSON. Para conectarse a un Firebase real, debes proveer el archivo `firebase_key.json` y configurar la variable de entorno correspondiente, como está detallado en `db.py`.*
