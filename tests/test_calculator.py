import unittest

from react_agent.calculator import safe_calc, CalcError


class TestSafeCalc(unittest.TestCase):
    # ---- 正确性 ----
    def test_basic(self):
        self.assertEqual(safe_calc("1 + 2"), 3)

    def test_precedence_and_paren(self):
        self.assertEqual(safe_calc("(12 + 8) * 3"), 60)

    def test_division(self):
        self.assertAlmostEqual(safe_calc("7 / 2"), 3.5)

    def test_floor_div_mod_pow(self):
        self.assertEqual(safe_calc("10 // 3"), 3)
        self.assertEqual(safe_calc("10 % 3"), 1)
        self.assertEqual(safe_calc("2 ** 10"), 1024)

    def test_unary(self):
        self.assertEqual(safe_calc("-5 + 3"), -2)
        self.assertEqual(safe_calc("+2 * -3"), -6)

    # ---- 安全性：必须拒绝 ----
    def test_reject_name(self):
        with self.assertRaises(CalcError):
            safe_calc("__import__('os')")

    def test_reject_call(self):
        with self.assertRaises(CalcError):
            safe_calc("open('/etc/passwd')")

    def test_reject_attribute(self):
        with self.assertRaises(CalcError):
            safe_calc("x.__class__")

    def test_reject_subscript(self):
        with self.assertRaises(CalcError):
            safe_calc("().__class__")

    def test_reject_assignment(self):
        with self.assertRaises(CalcError):
            safe_calc("a = 1")

    def test_reject_bool_constant(self):
        # True/False 是 bool，不允许作为数值
        with self.assertRaises(CalcError):
            safe_calc("True")

    def test_empty(self):
        with self.assertRaises(CalcError):
            safe_calc("")


if __name__ == "__main__":
    unittest.main()
