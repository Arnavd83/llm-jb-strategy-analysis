"""Unified LLM client for multiple providers."""

import os
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
import json

# Import provider libraries
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from together import Together
except ImportError:
    Together = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .config import LLMConfig


@dataclass
class LLMResponse:
    """Standardized response from LLM."""
    content: str
    raw_response: Optional[Dict] = None
    usage: Optional[Dict] = None


class LLMClient:
    """Unified client for interacting with different LLM providers."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate client based on provider."""
        provider = self.config.provider.lower()
        
        if provider == "openai":
            if openai is None:
                raise ImportError("OpenAI library not installed. Run: pip install openai")
            self._client = openai.OpenAI(api_key=self.config.api_key)
            
        elif provider == "anthropic":
            if anthropic is None:
                raise ImportError("Anthropic library not installed. Run: pip install anthropic")
            self._client = anthropic.Anthropic(api_key=self.config.api_key)
            
        elif provider == "together":
            if Together is None:
                raise ImportError("Together library not installed. Run: pip install together")
            self._client = Together(api_key=self.config.api_key)
            
        elif provider in ["google", "gemini"]:
            if genai is None:
                raise ImportError("Google GenerativeAI library not installed. Run: pip install google-generativeai")
            genai.configure(api_key=self.config.api_key)
            self._client = genai.GenerativeModel(self.config.model)
            
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def generate(
        self,
        messages: Union[str, List[Dict[str, str]]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate a response from the LLM.
        
        Args:
            messages: Either a string prompt or list of message dicts with 'role' and 'content'
            temperature: Override config temperature
            max_tokens: Override config max_tokens
            system_prompt: System prompt to prepend (if messages is a string)
            
        Returns:
            LLMResponse with generated content
        """
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        
        # Convert string to messages format
        if isinstance(messages, str):
            formatted_messages = []
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})
            formatted_messages.append({"role": "user", "content": messages})
        else:
            formatted_messages = messages
            if system_prompt and not any(m["role"] == "system" for m in formatted_messages):
                formatted_messages = [{"role": "system", "content": system_prompt}] + formatted_messages
        
        provider = self.config.provider.lower()
        
        try:
            if provider == "openai":
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=formatted_messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return LLMResponse(
                    content=response.choices[0].message.content,
                    raw_response=response.model_dump() if hasattr(response, 'model_dump') else None,
                    usage=response.usage.model_dump() if hasattr(response.usage, 'model_dump') else None
                )
                
            elif provider == "anthropic":
                # Anthropic requires system prompt separately
                system = None
                user_messages = []
                for msg in formatted_messages:
                    if msg["role"] == "system":
                        system = msg["content"]
                    else:
                        user_messages.append(msg)
                
                response = self._client.messages.create(
                    model=self.config.model,
                    messages=user_messages,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return LLMResponse(
                    content=response.content[0].text,
                    raw_response={"content": response.content, "usage": response.usage} if hasattr(response, 'usage') else None
                )
                
            elif provider == "together":
                # Together AI uses OpenAI-compatible format
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=formatted_messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return LLMResponse(
                    content=response.choices[0].message.content,
                    raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
                )
                
            elif provider in ["google", "gemini"]:
                # Google Gemini has a different format
                # Convert messages to Gemini format
                prompt_parts = []
                for msg in formatted_messages:
                    if msg["role"] == "system":
                        prompt_parts.append(f"System: {msg['content']}")
                    elif msg["role"] == "user":
                        prompt_parts.append(f"User: {msg['content']}")
                    elif msg["role"] == "assistant":
                        prompt_parts.append(f"Assistant: {msg['content']}")
                
                prompt = "\n\n".join(prompt_parts)
                
                generation_config = genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
                
                response = self._client.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                return LLMResponse(
                    content=response.text,
                    raw_response={"candidates": response.candidates} if hasattr(response, 'candidates') else None
                )
                
        except Exception as e:
            # Log error and re-raise
            print(f"Error generating response with {provider}: {str(e)}")
            raise
    
    def generate_json(
        self,
        messages: Union[str, List[Dict[str, str]]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """Generate a JSON response from the LLM.
        
        This method ensures the response is valid JSON.
        """
        # Add JSON instruction to prompt
        json_instruction = "\n\nPlease respond with valid JSON only, no additional text."
        
        if isinstance(messages, str):
            messages = messages + json_instruction
        else:
            # Add to last user message
            for i in range(len(messages) - 1, -1, -1):
                if messages[i]["role"] == "user":
                    messages[i]["content"] += json_instruction
                    break
        
        response = self.generate(messages, temperature, max_tokens, system_prompt)
        
        # Try to parse JSON
        try:
            # Clean response - remove markdown code blocks if present
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {response.content}")
            raise ValueError(f"Invalid JSON response: {e}")
