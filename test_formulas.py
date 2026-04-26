import unittest
from formulas import FinancialCalculator

class TestFinancialCalculator(unittest.TestCase):

    def test_calculate_price_from_margin(self):
        cost = 100.0
        margin = 0.20
        price = FinancialCalculator.calculate_price_from_margin(cost, margin)
        self.assertAlmostEqual(price, 125.0, places=2)

        with self.assertRaises(ValueError):
            FinancialCalculator.calculate_price_from_margin(cost, 1.0)
        with self.assertRaises(ValueError):
            FinancialCalculator.calculate_price_from_margin(cost, 1.5)
        with self.assertRaises(ValueError):
            FinancialCalculator.calculate_price_from_margin(cost, -0.1)

    def test_calculate_mpd_cost(self):
        # 10kg at 5 Bs/kg with 20% waste (merma)
        res = FinancialCalculator.calculate_mpd_cost(10.0, 5.0, 0.20)
        self.assertAlmostEqual(res["cantidad_final_kg"], 8.0, places=2)
        self.assertAlmostEqual(res["costo_total_bs"], 50.0, places=2)

        with self.assertRaises(ValueError):
            FinancialCalculator.calculate_mpd_cost(10.0, 5.0, 1.20)

    def test_calculate_full_costing(self):
        res = FinancialCalculator.calculate_full_costing(
            total_mpd_bs=5000.0,
            total_empaque_bs=1500.0,
            total_mod_bs=600.0,
            total_cif_bs=450.0,
            lote_produccion_unidades=1000,
            margen_fika_porcentaje=0.30,
            margen_pdv_porcentaje=0.20,
            impuestos_porcentaje=0.16
        )

        self.assertEqual(res["costos_totales"]["total_produccion"], 7550.0)
        self.assertEqual(res["costos_unitarios"]["costo_produccion"], 7.55)

        # PV Fabrica = 7.55 / (1 - 0.3) = 10.7857
        self.assertAlmostEqual(res["rentabilidad_unitaria"]["precio_venta_fabrica_bs"], 10.7857, places=3)
        # PV Publico Sin Impuestos = 10.7857 / (1 - 0.2) = 13.482
        self.assertAlmostEqual(res["rentabilidad_unitaria"]["precio_venta_publico_sin_impuestos_bs"], 13.482, places=3)
        # PV Publico = 13.482 / (1 - 0.16) = 16.05
        self.assertAlmostEqual(res["rentabilidad_unitaria"]["precio_venta_publico_bs"], 16.05, places=2)

        with self.assertRaises(ValueError):
             FinancialCalculator.calculate_full_costing(
                total_mpd_bs=5000.0,
                total_empaque_bs=1500.0,
                total_mod_bs=600.0,
                total_cif_bs=450.0,
                lote_produccion_unidades=0,
                margen_fika_porcentaje=0.30,
                margen_pdv_porcentaje=0.20,
                impuestos_porcentaje=0.16
            )

if __name__ == '__main__':
    unittest.main()
