"""Meaningful offline checks for benchmark isolation and citation boundaries."""
import unittest
from collections import Counter
from .common import BASE, read
from .pipeline import PageStore, validate_answer, enforce_numeric_fulfillment
from .run import verify_benchmark

class Contract(unittest.TestCase):
    def test_frozen_benchmark_and_group_minima(self):
        verify_benchmark()
        gold = read(BASE / "benchmarks/test.gold.json")
        self.assertEqual(Counter(q['primary_group'] for q in gold),
            Counter(table=6,diagram=5,chart=5,multi_hop=4,text=4,unanswerable=6))
        for split in ("dev","test"):
            inputs = read(BASE / f"benchmarks/{split}.inputs.json")
            self.assertTrue(all(set(q)=={'id','question'} for q in inputs))
    def test_cross_split_questions_are_distinct(self):
        dev = read(BASE / "benchmarks/dev.inputs.json")
        test = read(BASE / "benchmarks/test.inputs.json")
        self.assertFalse({q['question'] for q in dev} & {q['question'] for q in test})
    def test_unviewed_citation_and_vague_region_rejected(self):
        answer = {'status':'answered','claims':[{'text':'A','citations':[{'source_id':'NASA-SE:p0023','locator':'Figure 2.5-1, Concept block','evidence':'Concept 8%'}]}]}
        with self.assertRaises(ValueError): validate_answer(answer,{'NASA-SE:p0024'})
        validate_answer(answer,{'NASA-SE:p0023'})
        answer['claims'][0]['citations'][0]['locator']='page'
        with self.assertRaises(ValueError): validate_answer(answer,{'NASA-SE:p0023'})
    def test_abstention_cannot_include_claims(self):
        with self.assertRaises(ValueError):
            validate_answer({'status':'abstain','claims':[{'text':'guess'}]},set())
    def test_exact_number_request_cannot_be_answered_qualitatively(self):
        t={'events':[]}
        answer={'status':'answered','claims':[{'text':'No fixed quantity is provided; see NPR 1234.5.'}]}
        self.assertEqual(enforce_numeric_fulfillment(answer,'What exact number is mandatory?',t)['status'],'abstain')
        quantity={'status':'answered','claims':[{'text':'The measured quantity is 42.'}]}
        self.assertEqual(enforce_numeric_fulfillment(quantity,'What exact number is specified?',t),quantity)
    def test_search_all_pages_and_exact_figure(self):
        store=PageStore()
        self.assertEqual(len(store.pages),297)
        rows=store.search('Figure 6.5-2 Five Elements of Configuration Management',4)
        self.assertIn(155,[r['page'] for r in rows])
        self.assertTrue(all('expected' not in r and 'evidence' not in r for r in rows))

if __name__=='__main__': unittest.main()
