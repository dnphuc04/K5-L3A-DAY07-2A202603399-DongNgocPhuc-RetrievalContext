import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from .pipeline import run

class FakeStore:
    pages=[{'text':'Source'}]*297
    def search(self,query,top_k):
        self.query=query
        return [{'id':'NASA-SE:p0023','page':23,'text':'Figure chart','score':1,'reference_match':2}]

def response(name,args):
    return {'id':'offline','model':'offline','usage':{},'choices':[{'finish_reason':'tool_calls','message':{
        'role':'assistant','content':None,'tool_calls':[{'id':'offline-call','type':'function',
        'function':{'name':name,'arguments':json.dumps(args)}}]}}]},1

class AgentContract(unittest.TestCase):
    def test_real_protocol_enforces_query_images_and_source_link(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'page.png';path.write_bytes(b'fixture image bytes')
            # The production trace requires a workspace-relative cache path.
            with patch('advanced.pipeline.BASE',Path(directory)/'advanced'),patch('advanced.pipeline.render',return_value=path):
                replies=[response('search',{'query':'untrusted rewrite'}),response('view_pages',{'source_ids':['NASA-SE:p0023']}),
                    response('submit_answer',{'status':'answered','claims':[{'text':'8%',
                     'citations':[{'source_id':'NASA-SE:p0023','locator':'Figure 2.5-1, Concept block','evidence':'Concept 8%'}]}]})]
                with patch('advanced.pipeline.request',side_effect=replies) as provider:
                    store=FakeStore();out=run('original question','offline-placeholder',store,{'model':'offline','top_k':4,'max_tools':4,'image_size':1400})
                self.assertEqual(store.query,'original question')
                self.assertEqual(out['status'],'answered')
                self.assertEqual(out['viewed_pages'],[23])
                messages=provider.call_args_list[-1].args[1]['messages']
                self.assertTrue(any(isinstance(m.get('content'),list) and any(p['type']=='image_url' for p in m['content']) for m in messages))
    def test_unretrieved_page_id_fails_without_render_or_answer(self):
        replies=[response('search',{'query':'x'}),response('view_pages',{'source_ids':['NASA-SE:p0013']})]
        with patch('advanced.pipeline.request',side_effect=replies),patch('advanced.pipeline.render') as renderer:
            out=run('question','offline-placeholder',FakeStore(),{'model':'offline','top_k':4,'max_tools':4,'image_size':1400})
        self.assertEqual(out['status'],'error');renderer.assert_not_called()

if __name__=='__main__':unittest.main()
