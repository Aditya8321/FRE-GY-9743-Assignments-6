"""Independent financial checks for the six Assignment 6 swap implementations.

Run from the repository root with ``python -m unittest discover -s tests -v``.
The flat-curve oracle uses closed-form coupon amounts, independently of the
valuation engines and their leg-decomposition implementation.
"""

import math
import unittest

from fixedincomelib.date import Date, Period, TermOrDate
from fixedincomelib.market.basics import (
    AccrualBasis, BusinessDayConvention, HolidayConvention,
)
from fixedincomelib.market.data_conventions import (
    CompoundingMethod, DataConventionOvernightIndexBasisSwap, DataConventionRFRSwap,
)
from fixedincomelib.market.registries import IndexFixingsManager, IndexRegistry
from fixedincomelib.product import ProductOvernightIndexBasisSwap, ProductRFRSwap, PayOrReceive
from fixedincomelib.product.product_factory import ProductFactory
from fixedincomelib.valuation.valuation_engine import ValuationRequest
from fixedincomelib.yield_curve.valuation_engine import (
    ValuationEngineProductOvernightIndexBasisSwap, ValuationEngineProductRfrSwap,
)


class FlatCurveModel:
    """Distinct, continuously compounded projection and funding curves."""

    def __init__(self, value_date, sofr=0.04, ff=0.03, funding=0.02):
        self.value_date = Date(value_date)
        self.rates = {"SOFR-1B": sofr, "FF-1B": ff, "TEST-FUNDING": funding}

    def discount_factor(self, index, payment_date):
        name = index if isinstance(index, str) else IndexRegistry.look_up_index_name(index)
        return math.exp(-self.rates[name] * (payment_date - self.value_date) / 365.0)


class FundingParameters:
    """Only the funding-selection interface consumed by the product engines."""

    def get_vp_from_build_method_collection(self, parameter_type):
        return self

    def get_funding_index(self, currency):
        return "TEST-FUNDING"


class SwapTestCase(unittest.TestCase):
    notional = 1_000_000.0

    def setUp(self):
        IndexFixingsManager().clear()

    def tearDown(self):
        IndexFixingsManager().clear()

    def rfr(self, start="2027-01-04", end="2027-07-06", fixed_rate=0.05,
            spread=0.001, pay_or_rec=PayOrReceive.RECEIVE, lag="2D",
            fixed_period="1Y", floating_period=None, fixed_basis="ACT/360"):
        return ProductRFRSwap(
            Date(start), TermOrDate(end), Period(lag), "SOFR-1B", fixed_rate,
            pay_or_rec, self.notional, Period(fixed_period), AccrualBasis(fixed_basis),
            None if floating_period is None else Period(floating_period),
            BusinessDayConvention("F"), HolidayConvention("USGS"), spread,
            CompoundingMethod.COMPOUND,
        )

    def basis(self, start="2027-01-04", end="2027-07-06", spread=0.001,
              pay_or_rec=PayOrReceive.RECEIVE, lag="2D", period1="1Y", period2=None):
        return ProductOvernightIndexBasisSwap(
            Date(start), TermOrDate(end), Period(lag), "SOFR-1B", "FF-1B", spread,
            pay_or_rec, self.notional, Period(period1), AccrualBasis("ACT/360"),
            None if period2 is None else Period(period2), BusinessDayConvention("F"),
            HolidayConvention("USGS"), CompoundingMethod.COMPOUND,
        )

    def value(self, product, value_date="2026-12-31", **rates):
        engine_type = (ValuationEngineProductRfrSwap if isinstance(product, ProductRFRSwap)
                       else ValuationEngineProductOvernightIndexBasisSwap)
        engine = engine_type(FlatCurveModel(value_date, **rates), FundingParameters(),
                             product, ValuationRequest.PV)
        engine.calculate_value()
        return engine

    def assertMoneyEqual(self, actual, expected):
        self.assertAlmostEqual(actual, expected, delta=1e-7)


class SwapConstructionTests(SwapTestCase):
    def test_rfr_has_independent_fixed_and_floating_schedules_and_payment_lag(self):
        product = self.rfr(end="2028-01-04", fixed_period="1Y", floating_period="3M")
        self.assertEqual(product.fixed_leg.num_cashflows(), 1)
        self.assertEqual(product.floating_leg.num_cashflows(), 4)
        self.assertEqual(product.fixed_leg.cashflow(0).payment_date.ISO(), "2028-01-06")
        self.assertEqual(product.floating_leg.cashflow(3).payment_date.ISO(), "2028-01-06")
        self.assertEqual(product.last_date.ISO(), "2028-01-06")
        self.assertEqual(product.fixed_leg.fixed_rate, 0.05)
        self.assertEqual(product.floating_leg.float_index, "SOFR-1B")
        self.assertEqual(product.floating_leg.cashflow(0).spread, 0.001)
        self.assertEqual(product.fixed_leg.notional, self.notional)

    def test_basis_preserves_leg_indices_frequencies_and_single_spread(self):
        product = self.basis(end="2028-01-04", period1="6M", period2="3M")
        self.assertEqual(product.floating_leg_1.num_cashflows(), 2)
        self.assertEqual(product.floating_leg_2.num_cashflows(), 4)
        self.assertEqual(product.floating_leg_1.float_index, "SOFR-1B")
        self.assertEqual(product.floating_leg_2.float_index, "FF-1B")
        self.assertEqual(product.floating_leg_1.cashflow(0).spread, 0.001)
        self.assertEqual(product.floating_leg_2.cashflow(0).spread, 0.0)
        self.assertEqual(product.floating_leg_1_wo_basis.cashflow(0).spread, 0.0)
        self.assertEqual(product.floating_leg_1_basis.fixed_rate, 0.001)
        self.assertEqual(product.last_date.ISO(), "2028-01-06")

    def test_round_trip_serialization_preserves_swap_terms_and_cashflow_dates(self):
        for original in (self.rfr(), self.basis()):
            with self.subTest(product=original.product_type):
                restored = type(original).deserialize(original.serialize())
                self.assertEqual(restored.serialize(), original.serialize())
                self.assertEqual(restored.last_date, original.last_date)


class AnalyticSwapValuationTests(SwapTestCase):
    def test_rfr_matches_closed_form_and_uses_its_fixed_day_count(self):
        product = self.rfr(fixed_basis="ACT/365")
        engine = self.value(product)
        days = Date("2027-07-06") - Date("2027-01-04")
        fixed_amount = self.notional * 0.05 * days / 365.0
        floating_amount = self.notional * (math.expm1(0.04 * days / 365.0)
                                           + 0.001 * days / 360.0)
        df = math.exp(-0.02 * (Date("2027-07-08") - Date("2026-12-31")) / 365.0)
        self.assertMoneyEqual(engine.value, (fixed_amount - floating_amount) * df)
        self.assertEqual(engine.cash, 0.0)

    def test_basis_uses_both_projection_curves_and_adds_leg1_spread_once(self):
        product = self.basis()
        engine = self.value(product)
        days = Date("2027-07-06") - Date("2027-01-04")
        amount = self.notional * (math.expm1(0.04 * days / 365.0)
                                  - math.expm1(0.03 * days / 365.0)
                                  + 0.001 * days / 360.0)
        df = math.exp(-0.02 * (Date("2027-07-08") - Date("2026-12-31")) / 365.0)
        self.assertMoneyEqual(engine.value, amount * df)
        self.assertEqual(engine.cash, 0.0)

    def test_basis_equal_projection_curves_reduce_to_spread_annuity(self):
        product = self.basis()
        engine = self.value(product, sofr=0.04, ff=0.04)
        days = Date("2027-07-06") - Date("2027-01-04")
        expected = (self.notional * 0.001 * days / 360.0
                    * math.exp(-0.02 * (Date("2027-07-08") - Date("2026-12-31")) / 365.0))
        self.assertMoneyEqual(engine.value, expected)

    def test_pay_receive_reverses_value_and_repeated_calculation_is_idempotent(self):
        for constructor in (self.rfr, self.basis):
            with self.subTest(product=constructor.__name__):
                receive = self.value(constructor(pay_or_rec=PayOrReceive.RECEIVE))
                pay = self.value(constructor(pay_or_rec=PayOrReceive.PAY))
                self.assertMoneyEqual(pay.value, -receive.value)
                before = receive.value
                receive.calculate_value()
                self.assertMoneyEqual(receive.value, before)

    def test_due_today_is_undiscounted_cash_and_expired_products_are_zero(self):
        IndexFixingsManager().insert_fixing("SOFR-1B", Date("2027-01-04"), 0.04)
        IndexFixingsManager().insert_fixing("FF-1B", Date("2027-01-04"), 0.03)
        products = [
            (self.rfr(end="2027-01-05", lag="0D"), self.notional * (0.05 - 0.04 - 0.001) / 360),
            (self.basis(end="2027-01-05", lag="0D"), self.notional * (0.04 + 0.001 - 0.03) / 360),
        ]
        for product, expected in products:
            with self.subTest(product=product.product_type):
                engine = self.value(product, value_date="2027-01-05")
                self.assertMoneyEqual(engine.value, expected)
                self.assertMoneyEqual(engine.cash, expected)
                expired = self.value(product, value_date="2027-01-06")
                self.assertEqual(expired.value, 0.0)
                self.assertEqual(expired.cash, 0.0)

    def test_settled_accrual_with_payment_lag_remains_pv_without_current_cash(self):
        IndexFixingsManager().insert_fixing("SOFR-1B", Date("2027-01-04"), 0.04)
        product = self.rfr(end="2027-01-05", lag="2D")
        engine = self.value(product, value_date="2027-01-05")
        expected = self.notional * (0.05 - 0.04 - 0.001) / 360 * math.exp(-0.02 * 2 / 365)
        self.assertMoneyEqual(engine.value, expected)
        self.assertEqual(engine.cash, 0.0)

    def test_signed_cashflow_report_reconciles_to_product_pv(self):
        for product in (self.rfr(pay_or_rec=PayOrReceive.PAY), self.basis()):
            with self.subTest(product=product.product_type):
                engine = self.value(product)
                rows = engine.create_cash_flows_report().content
                self.assertMoneyEqual(sum(row["PV"] for row in rows), engine.value)


class ProductFactoryTests(SwapTestCase):
    @staticmethod
    def rfr_convention():
        return DataConventionRFRSwap("TEST-OIS", {
            "INDEX": "SOFR-1B", "ACCRUAL_BASIS": "ACT/365", "ACCRUAL_PERIOD": "6M",
            "PAYMENT_OFFSET": "3D", "PAYMENT_BUSINESS_DAY_CONVENTION": "MF",
            "PAYMENT_HOLIDAY_CONVENTION": "USGS", "COMPOUNDING_METHOD": "ARITHMETIC",
        })

    @staticmethod
    def basis_convention():
        return DataConventionOvernightIndexBasisSwap("TEST-BASIS", {
            "BASIS_OI_INDEX": "SOFR-1B", "REFERENCE_OI_INDEX": "FF-1B",
            "ACCRUAL_BASIS": "ACT/360", "ACCRUAL_PERIOD_1": "6M", "ACCRUAL_PERIOD_2": "3M",
            "PAYMENT_OFFSET": "3D", "PAYMENT_BUSINESS_DAY_CONVENTION": "MF",
            "PAYMENT_HOLIDAY_CONVENTION": "USGS", "COMPOUNDING_METHOD": "ARITHMETIC",
        })

    def test_rfr_factory_maps_all_convention_fields_and_trade_overrides(self):
        product = ProductFactory.create_product_from_data_convention(
            Date("2026-10-28"), "2Y", self.rfr_convention(), 0.037,
            notional=2_000_000.0, pay_or_rec="pay", spread=0.002,
        )
        self.assertIsInstance(product, ProductRFRSwap)
        self.assertEqual(product.effective_date.ISO(), "2026-10-28")
        self.assertEqual(product.termination_date.ISO(), "2028-10-30")
        self.assertEqual(product.fixed_rate, 0.037)
        self.assertEqual(product.spread, 0.002)
        self.assertEqual(product.notional, 2_000_000.0)
        self.assertEqual(product.pay_or_rec, PayOrReceive.PAY)
        self.assertEqual(str(product.accrual_period), "6M")
        self.assertEqual(str(product.pay_offset), "3D")
        self.assertEqual(product.accrual_basis.value_str, "ACT/365")
        self.assertEqual(product.pay_business_day_convention.value_str, "MF")
        self.assertEqual(product.compounding_method, CompoundingMethod.ARITHMETIC)

    def test_start_offset_times_tenor_uses_tenor_from_forward_start(self):
        for convention in (self.rfr_convention(), self.basis_convention()):
            with self.subTest(convention=convention.type()):
                product = ProductFactory.create_product_from_data_convention(
                    Date("2026-10-28"), "6M x 1Y", convention, 0.001,
                )
                self.assertEqual(product.effective_date.ISO(), "2027-04-28")
                self.assertEqual(product.termination_date.ISO(), "2028-04-28")

    def test_basis_factory_maps_quoted_spread_both_indices_and_each_frequency(self):
        product = ProductFactory.create_product_from_data_convention(
            Date("2026-10-28"), "2027-01-04x2028-01-04", self.basis_convention(), 0.0015,
            notional=500_000.0, pay_or_rec="pay",
        )
        self.assertIsInstance(product, ProductOvernightIndexBasisSwap)
        self.assertEqual(product.effective_date.ISO(), "2027-01-04")
        self.assertEqual(product.termination_date.ISO(), "2028-01-04")
        self.assertEqual(product.spread, 0.0015)
        self.assertEqual(product.notional, 500_000.0)
        self.assertEqual(product.pay_or_rec, PayOrReceive.PAY)
        self.assertEqual(product.floating_leg_1.float_index, "SOFR-1B")
        self.assertEqual(product.floating_leg_2.float_index, "FF-1B")
        self.assertEqual(str(product.accrual_period_leg_1), "6M")
        self.assertEqual(str(product.accrual_period_leg_2), "3M")
        self.assertEqual(str(product.pay_offset), "3D")
        self.assertEqual(product.compounding_method, CompoundingMethod.ARITHMETIC)


if __name__ == "__main__":
    unittest.main()
