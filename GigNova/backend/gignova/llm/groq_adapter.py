#!/usr/bin/env python3
"""
GigNova: Groq LLM Adapter
Provides integration with Groq LLM models for GigNova agents
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from gignova.config.settings import Settings

# Configure logging
logger = logging.getLogger(__name__)

class GroqAdapter:
    """Adapter for Groq LLM models"""
    
    def __init__(self, model_name: str = "llama3-70b-8192"):
        """Initialize Groq adapter with specified model"""
        self.model_name = model_name
        self.api_key = Settings.GROQ_API_KEY
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment variables")
            # Use a placeholder API key for testing environments
            self.api_key = "test_key_for_mock_usage_only"
        
        try:
            self.llm = ChatGroq(
                groq_api_key=self.api_key,
                model_name=self.model_name
            )
            logger.info(f"Initialized Groq adapter with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Groq adapter: {e}")
            # Create a placeholder for testing environments
            self.llm = None
    
    async def generate_text(self, 
                     prompt: str, 
                     system_prompt: Optional[str] = None,
                     temperature: float = 0.7,
                     max_tokens: int = 1024) -> str:
        """
        Generate text using Groq model
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        try:
            # Check if LLM is initialized
            if self.llm is None:
                logger.warning("LLM not initialized, returning mock response for testing")
                return f"Mock response for: {prompt}"
                
            messages = []
            
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
                
            messages.append(HumanMessage(content=prompt))
            
            # Configure model parameters
            self.llm.model_kwargs = {
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Generate response
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating text with Groq: {e}")
            return f"Error: {str(e)}"
    
    async def generate_structured_output(self, 
                                  prompt: str, 
                                  system_prompt: Optional[str] = None,
                                  output_schema: Dict[str, Any] = None,
                                  temperature: float = 0.2) -> Dict[str, Any]:
        """
        Generate structured output using Groq model
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt for context
            output_schema: Schema for structured output
            temperature: Sampling temperature (lower for more deterministic outputs)
            
        Returns:
            Structured output as dictionary
        """
        try:
            # Check if LLM is initialized
            if self.llm is None and output_schema is not None:
                logger.warning("LLM not initialized, returning mock structured response for testing")
                # Generate a mock response that matches the schema
                mock_response = {}
                for key, value_type in output_schema.items():
                    if isinstance(value_type, str) and value_type == "str":
                        mock_response[key] = f"Mock {key} for testing"
                    elif isinstance(value_type, str) and value_type == "int":
                        mock_response[key] = 42
                    elif isinstance(value_type, str) and value_type == "bool":
                        mock_response[key] = True
                    elif isinstance(value_type, list):
                        mock_response[key] = [f"Mock {key} item 1", f"Mock {key} item 2"]
                    elif isinstance(value_type, dict):
                        mock_response[key] = {k: "mock value" for k in value_type.keys()}
                return mock_response
            
            # Create prompt with schema instructions
            schema_instruction = f"Return a JSON object matching this schema: {output_schema}"
            full_prompt = f"{prompt}\n\n{schema_instruction}"
            
            # Generate response
            response = await self.generate_text(
                prompt=full_prompt,
                system_prompt=system_prompt,
                temperature=temperature
            )
            
            # Parse JSON response
            import json
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from response: {response}")
                return {"error": "Failed to parse structured output", "raw_response": response}
                
        except Exception as e:
            logger.error(f"Error generating structured output with Groq: {e}")
            return {"error": str(e)}

# Create singleton instance
groq_adapter = GroqAdapter()
