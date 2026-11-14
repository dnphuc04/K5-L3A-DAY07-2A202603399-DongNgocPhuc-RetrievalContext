import json
import unittest
from collections import Counter
from .common import BASE,read,verify_benchmark
from .pipeline import decode,accept,PageStore

class Contract(unittest.TestCase):
    def test_legacy_and_new_benchmark_frozen(self):
        verify_benchmark()
        gold=read(BASE/'benchmarks/test.gold.json')
        self.assertEqual(Counter(q['primary_group'] for q in gold),Counter(table=6,diagram=5,chart=5,multi_hop=4,text=4,unanswerable=6))
        for split in ['dev','test']:
            self.assertTrue(all(set(q)=={'id','question'} for q in read(BASE/f'benchmarks/{split}.inputs.json')))
    def test_conflicting_json_is_never_silently_chosen(self):
        a={'status':'abstain','claims':[]};s=json.dumps(a)
        self.assertEqual(decode('```json\n'+s+'\n```'),a)
        self.assertEqual(decode(s+'\n'+s),a)
        with self.assertRaises(ValueError):decode(s+'\n'+json.dumps({'status':'answered','claims':[]}))
        with self.assertRaises(ValueError):decode('{"status":')
    def test_citations_must_be_viewed_and_abstention_empty(self):
        a={'status':'answered','claims':[{'text':'Fact','citations':[{'source_id':'NASA-SE:p0103','locator':'Methods of Verification / Analysis','evidence':'Analysis'}]}]}
        with self.assertRaises(ValueError):accept(a,{'NASA-SE:p0136'})
        accept(a,{'NASA-SE:p0103'})
        with self.assertRaises(ValueError):accept({'status':'abstain','claims':a['claims']},{'NASA-SE:p0103'})
    def test_exact_heading_over_generic_topic(self):
        store=PageStore()
        rows=store.search('Methods of Verification analysis prototype not available',7)
        self.assertEqual(rows[0]['page'],103)
        with self.assertRaises(ValueError):store.region('NASA-SE:p0103',[.6,.2,.1,.4])

if __name__=='__main__':unittest.main()
