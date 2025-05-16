import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from llm import generate_answer_async, generate_answers_batch, generate_answer, generate_answers_batch_sync

class TestLLMAsync(unittest.TestCase):
    def setUp(self):
        self.mock_response = MagicMock()
        self.mock_response.choices = [MagicMock()]
        self.mock_response.choices[0].message.content = "Test response"
        self.mock_response.usage = MagicMock()
        self.mock_response.usage.total_tokens = 42

    def test_generate_answer_async(self):
        async def _test():
            mock_create = AsyncMock(return_value=self.mock_response)
            with patch('openai.chat.completions.create', mock_create):
                result = await generate_answer_async(
                    question="Test question",
                    context="Test context",
                    model="gpt-3.5-turbo"
                )
                
                self.assertEqual(result, "Test response")
                mock_create.assert_called_once()
        
        asyncio.run(_test())

    def test_generate_answers_batch(self):
        async def _test():
            mock_create = AsyncMock(return_value=self.mock_response)
            with patch('openai.chat.completions.create', mock_create):
                queries = [
                    {"question": "Q1", "context": "C1"},
                    {"question": "Q2", "context": "C2"}
                ]
                
                results = await generate_answers_batch(queries)
                
                self.assertEqual(len(results), 2)
                self.assertEqual(results, ["Test response", "Test response"])
                self.assertEqual(mock_create.call_count, 2)
        
        asyncio.run(_test())

    def test_generate_answer_sync(self):
        with patch('llm.generate_answer_async') as mock_async:
            mock_async.return_value = "Test response"
            
            result = generate_answer("Test question", "Test context")
            
            self.assertEqual(result, "Test response")
            mock_async.assert_called_once()

    def test_generate_answers_batch_sync(self):
        with patch('llm.generate_answers_batch') as mock_async:
            mock_async.return_value = ["Test response 1", "Test response 2"]
            
            queries = [
                {"question": "Q1", "context": "C1"},
                {"question": "Q2", "context": "C2"}
            ]
            
            results = generate_answers_batch_sync(queries)
            
            self.assertEqual(len(results), 2)
            self.assertEqual(results, ["Test response 1", "Test response 2"])
            mock_async.assert_called_once()

if __name__ == '__main__':
    unittest.main() 