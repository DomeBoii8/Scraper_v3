"""
LLM client using Ollama
"""

from langchain_ollama import OllamaLLM
import sys

# Initialize LLM
llm = OllamaLLM(
    model="gemma3:12b",
    temperature=0.2,
    timeout=120
)

def get_llm():
    """Get the LLM instance"""
    return llm

def invoke_llm(prompt):
    """
    Call LLM with prompt
    
    Args:
        prompt: str - Formatted prompt
        
    Returns:
        str: LLM response
    """
    try:
        response = llm.invoke(prompt)
        return response
    except Exception as e:
        return None