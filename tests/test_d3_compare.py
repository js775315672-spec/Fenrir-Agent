import json
import unittest
from fenrir.d3_compare import cases,grade,expected,PUBLIC

class D3Tests(unittest.TestCase):
    def test_balanced(self):
        _,samples=cases()
        self.assertEqual(len(samples),6)
        self.assertEqual(sum(c["observed"]!=expected(c) for c in samples),3)
    def test_modes_and_false_arithmetic(self):
        _,samples=cases()
        c=samples[1]
        x=dict(risk="possible_digit_integer_conflict",test_a=81,test_b=9,rationale="The digit instruction could conflict with an integer answer.")
        self.assertNotIn((9,81),PUBLIC)
        self.assertTrue(grade(c,"hybrid",json.dumps(x))["pass"])
        self.assertFalse(grade(c,"hybrid",json.dumps(dict(x,risk="no_mismatch_in_this_case")))["pass"])
        direct=dict(x,expected=expected(c),observed=c["observed"],mismatch=True,test_expected="90")
        self.assertTrue(grade(c,"direct",json.dumps(direct))["pass"])
        self.assertFalse(grade(c,"direct",json.dumps(dict(direct,expected="0")))["pass"])
        self.assertFalse(grade(c,"hybrid",json.dumps(dict(x,test_a=11,test_b=2)))["pass"])
