import os
import time
import re
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from typing import Any, List, Optional

def get_llm() -> BaseChatModel:
    """Returns the LLM, wrapped with automatic rate-limit retry."""
    provider = os.getenv("LLM_PROVIDER", "google").lower()
    
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        base_llm = ChatOpenAI(model=model, temperature=0)
        
    elif provider == "groq":
        from langchain_groq import ChatGroq
        model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        base_llm = ChatGroq(model=model, temperature=0)
        
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        model = os.getenv("LLM_MODEL", "llama3.1")
        base_llm = ChatOllama(model=model, temperature=0)
        
    else:  # google
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = os.getenv("LLM_MODEL", "gemini-2.0-flash")
        base_llm = ChatGoogleGenerativeAI(model=model, temperature=0)
    
    return RateLimitRetryLLM(base_llm=base_llm)


class RateLimitRetryLLM(BaseChatModel):
    """Wraps any LangChain chat model with automatic rate-limit retry + backoff."""
    base_llm: Any
    max_retries: int = 5

    @property
    def _llm_type(self) -> str:
        return "rate-limit-retry-wrapper"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return self.base_llm._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "rate" in error_str.lower():
                    # Extract retry delay from error message
                    wait_time = 60  # default
                    match = re.search(r'retry\s*(?:in|after|delay)[\s:]*(\d+)', error_str, re.IGNORECASE)
                    if match:
                        wait_time = int(match.group(1)) + 5  # add 5s buffer
                    
                    print(f"\n[Rate Limit] Hit API quota. Waiting {wait_time}s before retry (attempt {attempt+1}/{self.max_retries})...")
                    time.sleep(wait_time)
                else:
                    raise  # Not a rate limit error, re-raise immediately
        
        # If we exhausted all retries, do one final attempt and let it raise
        return self.base_llm._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    def bind_tools(self, tools, **kwargs):
        """Delegate bind_tools to the base LLM so ReAct agents work."""
        result = self.base_llm.bind_tools(tools, **kwargs)
        return result

    def with_structured_output(self, schema, **kwargs):
        """Delegate with_structured_output to the base LLM so Supervisor routing works."""
        return self.base_llm.with_structured_output(schema, **kwargs)

    @property
    def _identifying_params(self):
        return {"base_llm": str(self.base_llm)}
