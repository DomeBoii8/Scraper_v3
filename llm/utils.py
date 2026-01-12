"""
Utility functions for JSON parsing
"""

import json

import re


def safe_json_loads(text: str):
    """
    Robustly parse JSON from LLM output
    Handles code fences and extracts JSON from text
    """
    
    if not text or not text.strip():
        raise ValueError("Empty LLM response")
    
    cleaned = text.strip()
    
    # Remove markdown code fences
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    
    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON object or array
    json_pattern = re.compile(r"(\{.*\}|\[.*\])", re.DOTALL)
    match = json_pattern.search(cleaned)
    
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    raise ValueError("Invalid JSON from LLM")