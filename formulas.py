# formulas.py

class FinancialCalculator:
    @staticmethod
    def calculate_price_from_margin(cost: float, margin_percentage: float) -> float:
        """
        Calcula el precio de venta basado en el costo y el margen sobre el precio.
        Fórmula: Precio = Costo / (1 - Margen)
        Maneja errores de división por cero si el margen es 100% o mayor.
        """
        if margin_percentage >= 1.0 or margin_percentage < 0.0:
            raise ValueError("El margen debe ser un valor entre 0 y 0.99 (0% a 99%)")
        return cost / (1 - margin_percentage)

    @staticmethod
    def calculate_mpd_cost(cantidad_inicial_kg: float, costo_unitario_bs: float, porcentaje_merma: float) -> dict:
        """
        Calcula el costo total de la materia prima directa, tomando en cuenta la merma.
        Retorna la cantidad final obtenida y el costo total.
        """
        if porcentaje_merma >= 1.0 or porcentaje_merma < 0.0:
            raise ValueError("La merma debe estar entre 0 y 0.99 (0% a 99%)")

        cantidad_final_kg = cantidad_inicial_kg * (1 - porcentaje_merma)
        costo_total_bs = cantidad_inicial_kg * costo_unitario_bs

        return {
            "cantidad_final_kg": cantidad_final_kg,
            "costo_total_bs": costo_total_bs
        }

    @staticmethod
    def calculate_full_costing(
        total_mpd_bs: float,
        total_empaque_bs: float,
        total_mod_bs: float,
        total_cif_bs: float,
        lote_produccion_unidades: int,
        margen_fika_porcentaje: float,
        margen_pdv_porcentaje: float,
        impuestos_porcentaje: float
    ) -> dict:
        """
        Realiza el costeo completo para un lote de producción y devuelve el desglose por unidad.
        """
        if lote_produccion_unidades <= 0:
            raise ValueError("El lote de producción debe ser mayor a 0")

        # Costos Totales de Producción
        costo_total_produccion_bs = total_mpd_bs + total_empaque_bs + total_mod_bs + total_cif_bs

        # Costo Unitario de Producción
        costo_unitario_produccion_bs = costo_total_produccion_bs / lote_produccion_unidades

        # Precio de Venta Fábrica (PVP Fábrica) aplicando Margen Fika
        precio_venta_fabrica_bs = FinancialCalculator.calculate_price_from_margin(
            cost=costo_unitario_produccion_bs,
            margin_percentage=margen_fika_porcentaje
        )

        # El Margen Fika en Bs.
        monto_margen_fika_bs = precio_venta_fabrica_bs - costo_unitario_produccion_bs

        # Ahora el Retailer/Distribuidor compra a Precio de Fábrica.
        # El Precio de Venta al Público (PVP) antes de impuestos se calcula aplicando el Margen PDV sobre el Precio de Venta Fábrica
        precio_venta_publico_sin_impuestos_bs = FinancialCalculator.calculate_price_from_margin(
            cost=precio_venta_fabrica_bs,
            margin_percentage=margen_pdv_porcentaje
        )

        # Margen PDV en Bs.
        monto_margen_pdv_bs = precio_venta_publico_sin_impuestos_bs - precio_venta_fabrica_bs

        # Impuestos (se aplica sobre el precio final de venta al público)
        # La fórmula correcta para agregar el impuesto sobre el precio final es similar a un margen.
        # Si el usuario quiere ganar 'precio_venta_publico_sin_impuestos_bs' neto,
        # y el estado se queda un porcentaje 'impuestos_porcentaje' del total cobrado:
        precio_venta_publico_bs = FinancialCalculator.calculate_price_from_margin(
            cost=precio_venta_publico_sin_impuestos_bs,
            margin_percentage=impuestos_porcentaje
        )

        # Monto Impuestos en Bs.
        monto_impuestos_bs = precio_venta_publico_bs - precio_venta_publico_sin_impuestos_bs

        return {
            "costos_totales": {
                "mpd": total_mpd_bs,
                "empaque": total_empaque_bs,
                "mod": total_mod_bs,
                "cif": total_cif_bs,
                "total_produccion": costo_total_produccion_bs
            },
            "costos_unitarios": {
                "mpd": total_mpd_bs / lote_produccion_unidades,
                "empaque": total_empaque_bs / lote_produccion_unidades,
                "mod": total_mod_bs / lote_produccion_unidades,
                "cif": total_cif_bs / lote_produccion_unidades,
                "costo_produccion": costo_unitario_produccion_bs
            },
            "rentabilidad_unitaria": {
                "monto_margen_fika_bs": monto_margen_fika_bs,
                "precio_venta_fabrica_bs": precio_venta_fabrica_bs,
                "monto_margen_pdv_bs": monto_margen_pdv_bs,
                "precio_venta_publico_sin_impuestos_bs": precio_venta_publico_sin_impuestos_bs,
                "monto_impuestos_bs": monto_impuestos_bs,
                "precio_venta_publico_bs": precio_venta_publico_bs
            }
        }
