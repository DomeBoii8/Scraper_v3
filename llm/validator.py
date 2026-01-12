"""
Validator for LLM extraction results
Provides feedback for self-healing loop
"""

import sys


def validate_extraction(llm_result, columns, cleaned_dom_sample, task_type):
    """
    Validate LLM extraction and generate feedback if needed
    
    Args:
        llm_result: dict - LLM output
        columns: list - Expected columns
        cleaned_dom_sample: str - Sample of original content for reference
        
    Returns:
        tuple: (is_valid: bool, feedback: str)
    """
    
    issues = []
    
    # Check 1: Has records?
    if not llm_result.get('records') or len(llm_result['records']) == 0:
        issues.append("No records extracted. Look more carefully through the content.")
    
    # Check 2: Records match column count?
    for i, record in enumerate(llm_result.get('records', [])):
        if len(record) != len(columns):
            issues.append(f"Record {i+1} has {len(record)} values but should have {len(columns)} (matching columns: {columns})")
            break  # Only report first mismatch
    
    # Check 3: Empty/null values?
    empty_count = 0
    for record in llm_result.get('records', []):
        for value in record:
            if not value or value == "null" or value == "None":
                empty_count += 1
    
    if empty_count > len(llm_result.get('records', [])) * 0.5:  # More than 50% empty
        issues.append(f"Too many empty values ({empty_count} found). Extract actual data from the content.")
    
    # Check 4: Duplicate records?
    records = llm_result.get('records', [])
    if len(records) != len(set(tuple(r) for r in records)):
        issues.append("Duplicate records found. Extract unique items only.")
    
    # Check 5: Very few records when content is long?
    if len(cleaned_dom_sample) > 1000 and len(records) < 3:
        issues.append(f"Content is long ({len(cleaned_dom_sample)} chars) but only {len(records)} records extracted. There might be more items to extract.")
    
    # Check 6: Product name makes sense?
    product = llm_result.get('product', '')
    if not product or product == "scraped_data" or product == "unknown":
        issues.append("Product name is generic. Use a descriptive name based on what you're extracting.")
    
    if issues:
        feedback = "ISSUES FOUND:\n" + "\n".join(f"- {issue}" for issue in issues)
        feedback += f"\n\nHINT: Look at this sample again:\n{cleaned_dom_sample[:500]}..."
        return False, feedback
    
    return True, None


def format_retry_prompt(original_prompt, feedback, previous_attempt):
    """
    Format a retry prompt with feedback
    
    Args:
        original_prompt: str - Original extraction prompt
        feedback: str - Validation feedback
        previous_attempt: dict - Previous LLM result
        
    Returns:
        str: New prompt with feedback
    """
    
    retry_prompt = f"""
{original_prompt}

⚠️ PREVIOUS ATTEMPT WAS INCORRECT ⚠️

Your previous extraction:
{previous_attempt}

FEEDBACK FROM VALIDATOR:
{feedback}

Please try again, addressing the issues above.
Remember:
1. Extract REAL data from the content
2. Look for ALL matching items
3. Ensure each record has the correct number of columns
4. Do not leave empty values if data exists
5. Extract multiple records if multiple items exist

Return ONLY valid JSON with the corrected extraction.
"""
    
    return retry_prompt
