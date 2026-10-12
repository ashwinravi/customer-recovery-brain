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
        with patch.object(brain,'indexing_status',return_value={'ready':True}),patch.object(brain,'hydra',return_value=client),patch.object(brain,'generate',return_value='Assessment [S1]') as model:
            result=brain.ask('What changed?')
            self.assertEqual(len(model.call_args.args[1]),1)
            self.assertEqual(model.call_args.args[1][0]['content'],'specific evidence')
            self.assertEqual(result['mode'],'HydraDB + LLM')

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

    def test_uncited_answer_is_rejected(self):
        fake=MagicMock()
        fake.chat.completions.create.return_value.choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='Unsupported answer'))]
        with patch.dict('os.environ',{'LLM_PROVIDER':'openai','LLM_API_KEY':'test','LLM_MODEL':'test'}),patch('openai.OpenAI',return_value=fake):
            with self.assertRaisesRegex(ValueError,'no cited answer'):
                brain.generate('Risk?',[{'label':'S1','content':'Evidence'}],{})

if __name__=='__main__': unittest.main()
