import openai
import os
import time
import asyncio
from typing import List, Dict, Any, Optional, Union
from metrics_tracker import get_metrics_tracker

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

openai.api_key = OPENAI_API_KEY

async def generate_answer_async(question: str, context: str, model: str = "gpt-3.5-turbo") -> str:
    """
    Asynchronously generate an answer using OpenAI's GPT model.
    Logs model name, input size, response time, and token usage for metrics tracking.
    """
    messages = [
        {"role": "system", "content": "You are a helpful AI sales assistant. Use the provided context to answer the user's question as accurately as possible. If the context is insufficient, say so."},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
    ]
    start_time = time.time()
    input_size = len(question) + len(context)
    tracker = get_metrics_tracker()
    try:
        response = await openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=512
        )
        latency = time.time() - start_time
        token_usage = None
        if hasattr(response, 'usage') and response.usage:
            token_usage = {
                'total_tokens': getattr(response.usage, 'total_tokens', None),
                'prompt_tokens': getattr(response.usage, 'prompt_tokens', None),
                'completion_tokens': getattr(response.usage, 'completion_tokens', None)
            }
        tracker.track_llm_call(model_name=model, input_size=input_size, latency=latency, success=True, token_usage=token_usage)
        return response.choices[0].message.content.strip()
    except Exception as e:
        latency = time.time() - start_time
        tracker.track_llm_call(model_name=model, input_size=input_size, latency=latency, success=False, error=str(e))
        raise

async def generate_answers_batch(queries: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> List[str]:
    """
    Process multiple queries in parallel using async/await.
    Each query should be a dict with 'question' and 'context' keys.
    """
    tasks = []
    for query in queries:
        task = generate_answer_async(
            question=query['question'],
            context=query['context'],
            model=model
        )
        tasks.append(task)
    return await asyncio.gather(*tasks)

def generate_answer(question: str, context: str, model: str = "gpt-3.5-turbo") -> str:
    """
    Synchronous wrapper for generate_answer_async.
    Maintains backward compatibility while enabling async usage.
    """
    return asyncio.run(generate_answer_async(question, context, model))

def generate_answers_batch_sync(queries: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> List[str]:
    """
    Synchronous wrapper for generate_answers_batch.
    Maintains backward compatibility while enabling async usage.
    """
    return asyncio.run(generate_answers_batch(queries, model)) 