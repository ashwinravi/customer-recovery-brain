import importlib.util
import unittest
import types
from pathlib import Path
from unittest.mock import patch, MagicMock

spec=importlib.util.spec_from_file_location('brain',Path(__file__).resolve().parents[1]/'app.py')
brain=importlib.util.module_from_spec(spec);spec.loader.exec_module(brain)

class WorkflowTests(unittest.TestCase):
    def test_pending_evidence_blocks_provider_calls(self):
        with patch.object(brain,'indexing_status',return_value={'ready':False}),patch.object(brain,'hydra') as client:
            with self.assertRaisesRegex(ValueError,'not fully indexed'):
                brain.ask('Why at risk?')
            client.assert_not_called()

    def test_local_preview_never_calls_live_services(self):
        with patch.object(brain,'hydra') as client,patch.object(brain,'generate') as model:
            result=brain.ask('support risk',local_only=True)
            self.assertEqual(result['mode'],'Local preview')
            self.assertGreater(len(result['evidence']),0)
            client.assert_not_called();model.assert_not_called()

    def test_live_generation_gets_only_retrieved_evidence(self):
        client=MagicMock();client.query.return_value={'success':True,'data':{'chunks':[{'source_title':'Retrieved note','chunk_content':'specific evidence','id':'x'}], 'graph_context':{'query_paths':[]}}}
        with patch.object(brain,'indexing_status',return_value={'ready':True}),patch.object(brain,'hydra',return_value=client),patch.object(brain,'plan_queries',return_value=[]),patch.object(brain,'generate',return_value='Assessment [S1]') as model:
            result=brain.ask('What changed?')
            self.assertEqual(len(model.call_args.args[1]),1)
            self.assertEqual(model.call_args.args[1][0]['content'],'specific evidence')
            self.assertEqual(result['mode'],'HydraDB + LLM')

    def test_followup_search_merges_only_new_evidence(self):
        first={'data':{'chunks':[{'source_title':'crm.md','chunk_content':'Green','id':'a'}],'graph_context':{}}}
        followup={'data':{'chunks':[{'source_title':'crm.md','chunk_content':'Green','id':'a'},{'source_title':'billing.md','chunk_content':'Renewal Nov 30','id':'b'}]}}
        client=MagicMock();client.query.side_effect=[first,followup]
        with patch.object(brain,'indexing_status',return_value={'ready':True}),patch.object(brain,'hydra',return_value=client),patch.object(brain,'plan_queries',return_value=['renewal status']),patch.object(brain,'generate',return_value='Assessment [S2]') as model:
            result=brain.ask('Is the renewal at risk?')
        self.assertEqual([e['title'] for e in model.call_args.args[1]],['crm.md','billing.md'])
        self.assertEqual([e['label'] for e in model.call_args.args[1]],['S1','S2'])
        self.assertEqual(result['steps'][1],{'query':'renewal status','new_sources':1})
        self.assertIn('renewal status',client.query.call_args.kwargs['query'])

    def test_malformed_plan_skips_followups(self):
        with patch.dict('os.environ',{'LLM_API_KEY':'test','LLM_MODEL':'test','AGENT_MAX_FOLLOWUPS':'2'}),patch.object(brain,'complete',return_value='not json'):
            self.assertEqual(brain.plan_queries('Risk?',[{'title':'crm.md','content':'Green'}]),[])

    def test_plan_is_capped_and_cleaned(self):
        with patch.dict('os.environ',{'LLM_API_KEY':'test','LLM_MODEL':'test','AGENT_MAX_FOLLOWUPS':'2'}),patch.object(brain,'complete',return_value='{"queries": ["renewal", " ", "sentiment", "root cause"]}'):
            self.assertEqual(brain.plan_queries('Risk?',[{'title':'crm.md','content':'Green'}]),['renewal','sentiment'])

    def test_missing_evidence_refuses_generation(self):
        client=MagicMock();client.query.return_value={'data':{'chunks':[]}}
        with patch.object(brain,'indexing_status',return_value={'ready':True}),patch.object(brain,'hydra',return_value=client),patch.object(brain,'generate') as model:
            with self.assertRaisesRegex(ValueError,'no evidence'):
                brain.ask('Anything?')
            model.assert_not_called()

    def test_invalid_citation_is_rejected(self):
        fake=MagicMock()
        fake.chat.completions.create.return_value.choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='Invented source [S9]'))]
        with patch.dict('os.environ',{'LLM_PROVIDER':'openai','LLM_API_KEY':'test','LLM_MODEL':'test'}),patch('openai.OpenAI',return_value=fake):
            with self.assertRaisesRegex(ValueError,'invalid source citation'):
                brain.generate('Risk?',[{'label':'S1','content':'Evidence'}],{})

    def test_invalid_citation_is_retried_once(self):
        fake=MagicMock()
        fake.chat.completions.create.side_effect=[types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=c))]) for c in ('Bad [S9]','Good [S1]')]
        with patch.dict('os.environ',{'LLM_PROVIDER':'openai','LLM_API_KEY':'test','LLM_MODEL':'test'}),patch('openai.OpenAI',return_value=fake):
            self.assertEqual(brain.generate('Risk?',[{'label':'S1','content':'Evidence'}],{}),'Good [S1]')
            self.assertEqual(fake.chat.completions.create.call_count,2)

    def test_uncited_answer_is_rejected(self):
        fake=MagicMock()
        fake.chat.completions.create.return_value.choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='Unsupported answer'))]
        with patch.dict('os.environ',{'LLM_PROVIDER':'openai','LLM_API_KEY':'test','LLM_MODEL':'test'}),patch('openai.OpenAI',return_value=fake):
            with self.assertRaisesRegex(ValueError,'no cited answer'):
                brain.generate('Risk?',[{'label':'S1','content':'Evidence'}],{})

if __name__=='__main__': unittest.main()
