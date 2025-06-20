#!/usr/bin/env python3
"""
GigNova: Groq Integration Example
Demonstrates how to use the Groq adapter for text generation and structured outputs
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from gignova
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gignova.llm import groq_adapter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def generate_job_description():
    """Generate a job description using Groq"""
    prompt = """
    Create a detailed job description for a Senior Backend Developer position 
    at a fintech startup. Include responsibilities, requirements, and benefits.
    """
    
    response = await groq_adapter.generate_text(
        prompt=prompt,
        system_prompt="You are an expert technical recruiter with deep knowledge of software engineering roles.",
        temperature=0.7
    )
    
    logger.info("Generated Job Description:")
    print("\n" + "="*50 + "\n")
    print(response)
    print("\n" + "="*50 + "\n")
    
    return response

async def generate_structured_job():
    """Generate a structured job description using Groq"""
    prompt = """
    Create a job description for a Data Scientist position at a healthcare AI company.
    """
    
    # Define the schema for the structured output
    schema = {
        "title": "str",
        "company": "str",
        "location": "str",
        "remote": "bool",
        "description": "str",
        "responsibilities": ["str"],
        "requirements": ["str"],
        "benefits": ["str"],
        "salary_range": {
            "min": "int",
            "max": "int",
            "currency": "str"
        }
    }
    
    response = await groq_adapter.generate_structured_output(
        prompt=prompt,
        system_prompt="You are an expert technical recruiter specializing in data science roles.",
        output_schema=schema,
        temperature=0.2  # Lower temperature for more deterministic structured output
    )
    
    logger.info("Generated Structured Job Description:")
    print("\n" + "="*50 + "\n")
    import json
    print(json.dumps(response, indent=2))
    print("\n" + "="*50 + "\n")
    
    return response

async def main():
    """Run the example"""
    # Load environment variables from .env file
    load_dotenv()
    
    # Check if GROQ_API_KEY is set
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY environment variable not set. Please add it to your .env file.")
        return
    
    # Generate a text job description
    await generate_job_description()
    
    # Generate a structured job description
    await generate_structured_job()

if __name__ == "__main__":
    asyncio.run(main())
