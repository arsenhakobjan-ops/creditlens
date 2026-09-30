import math
import unittest
from engine import evaluate, payment

BASE = dict(income=450000, expenses=180000, existing_debt=40000,
            amount=2000000, annual_rate=18, months=36, late_days=0)

class Rules(unittest.TestCase):
    def test_stable_pass(self):
        r = evaluate(BASE)
        self.assertEqual(r['decision'], 'PASS')
        self.assertNotIn('score', r)
    def test_overdue_review(self):
        self.assertEqual(evaluate(dict(BASE, late_days=10))['decision'], 'REVIEW')
    def test_overdue_30_is_review(self):
        self.assertEqual(evaluate(dict(BASE, late_days=30))['decision'], 'REVIEW')
    def test_overdue_31_declines(self):
        self.assertEqual(evaluate(dict(BASE, late_days=31))['decision'], 'HIGH_RISK')
    def test_negative_surplus_declines(self):
        self.assertEqual(evaluate(dict(BASE, expenses=450000))['decision'], 'HIGH_RISK')
    def test_dti_50_boundary(self):
        x=dict(BASE, amount=120000, annual_rate=0, months=12, existing_debt=0, income=20000, expenses=0)
        self.assertEqual(evaluate(x)['decision'], 'REVIEW')
        self.assertEqual(evaluate(dict(x,income=19999))['decision'], 'HIGH_RISK')
    def test_dti_35_boundary(self):
        x=dict(BASE, amount=42000, annual_rate=0, months=12, existing_debt=0, income=10000, expenses=0)
        self.assertEqual(evaluate(x)['decision'], 'PASS')
        self.assertEqual(evaluate(dict(x,amount=42001))['decision'], 'REVIEW')
    def test_small_remainder_review(self):
        self.assertEqual(evaluate(dict(BASE,expenses=310000))['decision'],'REVIEW')
    def test_remainder_15_boundary(self):
        x=dict(BASE,income=100000,expenses=75000,existing_debt=0,amount=120000,annual_rate=0,months=12)
        self.assertEqual(evaluate(x)['decision'],'PASS')
        self.assertEqual(evaluate(dict(x,expenses=75001))['decision'],'REVIEW')
    def test_zero_remainder_review(self):
        x=dict(BASE,income=100000,expenses=90000,existing_debt=0,amount=120000,annual_rate=0,months=12)
        self.assertEqual(evaluate(x)['decision'],'REVIEW')
    def test_total_debt_includes_existing(self):
        r=evaluate(BASE)
        self.assertAlmostEqual(r['total_monthly_debt'],r['monthly_payment']+BASE['existing_debt'],places=2)
    def test_high_risk_overrides_review(self):
        r=evaluate(dict(BASE,expenses=310000,late_days=31))
        self.assertEqual(r['decision'],'HIGH_RISK')
        self.assertEqual(len(r['reasons']),2)
    def test_decimal_surplus_is_preserved(self):
        x=dict(BASE,income=100000,expenses=89999.5,existing_debt=0,amount=120000,annual_rate=0,months=12)
        self.assertEqual(evaluate(x)['disposable_income'],.5)
    def test_zero_rate(self):
        self.assertEqual(payment(120000, 0, 12), 10000)
    def test_annuity_reference(self):
        # Independently checked reference: 2m AMD, 18% nominal, 36 months.
        self.assertAlmostEqual(payment(2000000,18,36), 72304.79, places=2)
    def test_tiny_rate(self):
        self.assertAlmostEqual(payment(120000,1e-12,12),10000,places=5)
    def test_missing_field(self):
        x=BASE.copy();x.pop('income')
        with self.assertRaises(ValueError): evaluate(x)
    def test_unknown_field(self):
        with self.assertRaises(ValueError): evaluate(dict(BASE,name='customer'))
    def test_non_numeric(self):
        for value in ('450000',None,True,[],{}):
            with self.subTest(value=value), self.assertRaises(ValueError): evaluate(dict(BASE,income=value))
    def test_non_finite(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError): evaluate(dict(BASE,income=value))
    def test_bounds(self):
        for k,v in [('income',0),('amount',0),('expenses',-1),('annual_rate',61),('months',361),('late_days',-1)]:
            with self.subTest(key=k), self.assertRaises(ValueError): evaluate(dict(BASE,**{k:v}))
    def test_fractional_integers(self):
        for k in ('months','late_days'):
            with self.subTest(key=k), self.assertRaises(ValueError): evaluate(dict(BASE,**{k:1.5}))
    def test_not_object(self):
        with self.assertRaises(ValueError): evaluate([])
    def test_input_unchanged(self):
        x=BASE.copy();evaluate(x);self.assertEqual(x,BASE)
    def test_payment_monotonic(self):
        self.assertGreater(payment(200000,18,12),payment(100000,18,12))
        self.assertGreater(payment(100000,24,12),payment(100000,18,12))
        self.assertGreater(payment(100000,18,12),payment(100000,18,24))

if __name__ == '__main__': unittest.main()
