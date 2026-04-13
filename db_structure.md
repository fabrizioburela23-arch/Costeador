# Estructura de Base de Datos NoSQL (Firebase Firestore)

Para soportar la persistencia de los costeos en Firebase Firestore y garantizar la escalabilidad de la "App Costeador", proponemos la siguiente estructura orientada a documentos.

## Colección Principal: `costeos`

Cada documento dentro de esta colección representará un análisis o "escenario de costeo" completo guardado por el usuario.

### Documento de Costeo (Ejemplo)

```json
{
  "id": "doc_id_auto_generado",
  "nombre_costeo": "Mango Deshidratado - Lote 100kg",
  "fecha_creacion": "2023-10-25T14:30:00Z",
  "lote_produccion_kg": 100, // Tamaño del lote de producción final

  "mpd": [
    {
      "nombre": "Mango fresco",
      "costo_unitario_bs": 5.0,
      "cantidad_inicial_kg": 1000,
      "porcentaje_merma": 0.90, // 90% de pérdida de agua/merma
      "cantidad_final_kg": 100,
      "costo_total_bs": 5000.0
    }
  ],

  "empaque": [
    {
      "item": "Bolsa Doypack",
      "costo_unitario_bs": 1.5,
      "cantidad": 1000,
      "costo_total_bs": 1500.0
    },
    {
      "item": "Etiqueta Frontal",
      "costo_unitario_bs": 0.5,
      "cantidad": 1000,
      "costo_total_bs": 500.0
    }
  ],

  "mod": {
    "tipo_calculo": "horas_hombre", // o "por_lote"
    "horas_hombre_totales": 40,
    "costo_por_hora_bs": 15.0,
    "costo_total_bs": 600.0
  },

  "cif": [
    {
      "concepto": "Energía Eléctrica (Deshidratador)",
      "costo_total_bs": 300.0
    },
    {
      "concepto": "Depreciación Máquinas",
      "costo_total_bs": 150.0
    }
  ],

  "parametros_financieros": {
    "margen_fika_porcentaje": 0.30, // 30%
    "margen_pdv_porcentaje": 0.20, // 20%
    "impuestos_porcentaje": 0.16 // 16% (O el porcentaje correspondiente según ley, aplicable al precio)
  },

  "resultados": {
    "costo_total_produccion_bs": 8050.0,
    "costo_unitario_produccion_bs": 8.05, // asumiendo 1000 unidades finales
    "precio_venta_fabrica_bs": 11.50, // Calculado con Margen Fika
    "precio_venta_publico_bs": 14.37, // Calculado con Margen PDV e Impuestos
    "monto_impuestos_bs": 2.30,
    "monto_margen_fika_bs": 3.45,
    "monto_margen_pdv_bs": 2.87
  }
}
```

### Justificación de la Estructura:
1. **Desnormalización Controlada:** Toda la información necesaria para recrear un costeo está autocontenida en un solo documento. Esto minimiza las lecturas a la base de datos (Firestore cobra por lectura) y hace que la carga de escenarios sea muy rápida.
2. **Flexibilidad en Arreglos (Arrays):** `mpd`, `empaque` y `cif` son arreglos de objetos. Esto permite agregar un número ilimitado de ingredientes, empaques o costos indirectos sin cambiar la estructura del esquema.
3. **Manejo Explicito de Mermas:** Dentro del objeto `mpd`, guardamos tanto la `cantidad_inicial_kg` como el `porcentaje_merma` para entender exactamente cómo la deshidratación afecta el costo real de la materia prima.
4. **Separación de Parámetros y Resultados:** Guardamos las tasas (`parametros_financieros`) y también los `resultados` calculados para tener un histórico estático de lo que costaba/valía en el momento de guardarlo, aunque las fórmulas cambien en el futuro.
