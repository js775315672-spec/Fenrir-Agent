import json
import unittest
from fenrir.d3_c5 import facts,TASKS,evaluate

class C5Tests(unittest.TestCase):
    def test_facts_are_source_bound(self):
        f=facts()
        self.assertEqual(len(f["rows"]),30)
        self.assertEqual(sum(r["mismatch"] for r in f["rows"]),10)
        self.assertEqual(f["rows"][0]["expected"],"13")
        self.assertFalse(f["rows"][0]["mismatch"])
        self.assertEqual(f["rows"][8]["expected"],"38")
        self.assertTrue(f["rows"][8]["mismatch"])
    def test_novel_proposal_and_fail_closed(self):
        task=TASKS[0]
        x={"hypothesis":"digit_instruction","a":20,"b":1}
        g=evaluate(task,json.dumps(x))
        self.assertTrue(g["pass"])
        self.assertEqual([a["expected"] for a in g["arms"]],["21","21"])
        self.assertFalse(g["test_executed"])
        for bad in (dict(a=True),dict(a=29,b=9),dict(a=20,b=5),dict(hypothesis="carry_difficulty"),dict(expected="21"),dict(a=40)):
            self.assertFalse(evaluate(task,json.dumps(dict(x,**bad)))["pass"])
        self.assertFalse(evaluate(task,'{"a":20,"a":21,"b":1,"hypothesis":"digit_instruction"}')["pass"])
    def test_carry_contrast(self):
        x={"hypothesis":"carry_difficulty","a":29,"b":2}
        g=evaluate(TASKS[1],json.dumps(x))
        self.assertTrue(g["pass"])
        self.assertEqual([a["expected"] for a in g["arms"]],["31","22"])
