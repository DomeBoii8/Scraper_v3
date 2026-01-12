# ============================================================================
# STAGE 1: SCRAPE PLANNING
# ============================================================================

SCRAPE_PLAN_PROMPT = """
You are a scraping planner.
Given a URL and a natural language user request, analyze and decide:

1. URL (repeat as-is)
2. Number of pages to scrape
3. Task type (structured_extraction, summarization, or hybrid)
4. What columns/data to extract (if structured extraction)
5. Output format preference

TASK TYPE DETECTION RULES:
- "structured_extraction": User wants specific data fields (products, prices, names, etc.)
- "summarization": User wants summary, overview, or content understanding
- "hybrid": User wants both structured data AND a summary

PAGINATION RULES:
- If pagination NOT mentioned → pages = 1
- If "all", "everything", "entire site" → pages = "ALL"
- If specific number mentioned → use that number
- For listing/product pages, default to checking at least 3-5 pages

COLUMN DETECTION:
- Analyze user request for explicit fields: "name", "price", "rating", etc.
- Infer common fields for the domain (e.g., products → name, price, description)
- If user says "all details" → extract comprehensive set of columns

OUTPUT FORMAT:
- Default: "json"
- If user mentions "csv", "excel", "table" → "csv"
- If user mentions "excel" -> "xlsx"
- If user mentions "table" -> "json"

URL: {url}
User request: {request}

Return STRICT JSON ONLY in this format:
{{
  "url": "<url>",
  "task_type": "<structured_extraction or summarization or hybrid>",
  "columns": [<List of required columns>],
  "include_summary": <boolean_type (True or False)>,
  "output_format": <OUTPUT_FORMAT>
}}

NO explanations, ONLY JSON!
"""

# ============================================================================
# STAGE 2: DATA EXTRACTION
# ============================================================================

CLEANED_DOM_EXTRACTION_PROMPT = """
You are an expert data extraction AI analyzing cleaned text content from a webpage.

The content has been cleaned using Trafilatura, so there are NO HTML tags.
You must analyze the PATTERNS in the text to extract structured data.

SCRAPE PLAN:
- Task Type: {task_type}
- Requested Columns: {columns}
- Include Summary: {include_summary}
- Output Format: {output_format}

CLEANED PAGE CONTENT (PAGE {current_page}/{total_pages}):
{cleaned_dom}

YOUR TASKS:
{task_instructions}

CRITICAL EXTRACTION RULES - READ CAREFULLY:

1. EXTRACT **ALL** MATCHING ITEMS FROM THE ENTIRE CONTENT
   - Scan the COMPLETE content from start to finish
   - Do NOT stop after finding 3-4 items
   - Do NOT use placeholder values like "value1", "value2", "value3"
   - Extract EVERY single item that matches the pattern

2. REAL DATA ONLY:
   - Use ACTUAL text from the content above
   - Each record must contain REAL values found in the content
   - If you find 50 products, extract all 50
   - If you find 200 products, extract all 200

3. PATTERN RECOGNITION:
   - Identify the repeating structure (e.g., product blocks)
   - Look for markers: prices ($, Rs, €), ratings (★, /5), etc.
   - Extract data systematically from each instance

4. DATA STRUCTURE:
   - "columns" must exactly match: {columns}
   - "records" is a list of lists: [["val1", "val2"], ["val3", "val4"], ...]
   - Each record must have exactly {num_columns} values (same as columns length)
   - Extract EVERY matching record in the content

5. COMPLETENESS:
   - Your job is to find ALL instances, not just examples
   - Continue extracting until you reach the end of the content
   - Empty records list [] only if genuinely NO matching data exists

6. SUMMARY (if requested):
   - Provide 2-5 sentences after extraction if task is to structurally extract with or without summarization (as mentioned in below examples)
   - KEEP IN MIND TO GENERATE 10-15 SENTENCES WITH APT TECHNICAL SPECS IF TASK IS TO ONLY SUMMARIZE (as mentioned below in example)
   - Include statistics (e.g., "Found 47 products ranging from $10-$500")

Return ONLY valid JSON in this EXACT format:
{{
  "product": "descriptive_name_of_what_you_extracted",
  "columns": {columns},
  "records": [
    ["actual_value_1", "actual_value_2"],
    ["actual_value_3", "actual_value_4"],
    ["actual_value_5", "actual_value_6"]
    // ... continue for ALL items found
  ],
  "summary": {summary_value},
  "page_info": {{
    "current_page": {current_page},
    "total_pages": {total_pages},
    "records_extracted": "NUMBER_OF_RECORDS_YOU_EXTRACTED"
  }},
  "outputFormat": "{output_format}"
}}

COMPLETE EXAMPLES:

Example 1 - Extracting ALL products (not just 2-3):
Input content has 10 kurtas listed
Output:
{{
  "product": "kurtas",
  "columns": ["name", "price"],
  "records": [
    ["Blue Cotton Kurta", "Rs 1299"],
    ["Red Silk Kurta", "Rs 2499"],
    ["Green Printed Kurta", "Rs 999"],
    ["Yellow Embroidered Kurta", "Rs 1899"],
    ["Black Kurta Set", "Rs 1599"],
    ["White Kurta", "Rs 1199"],
    ["Pink Kurta", "Rs 1399"],
    ["Purple Kurta", "Rs 1799"],
    ["Orange Kurta", "Rs 1099"],
    ["Grey Kurta", "Rs 1299"]
  ],
  "summary": null,
  "page_info": {{"current_page": 1, "total_pages": 1, "records_extracted": "10"}},
  "outputFormat": "json"
}}

Example 2 - With summary (extracting ALL items):
Input has 25 smartphones
Output:
{{
  "product": "smartphones",
  "columns": ["model", "price", "rating"],
  "records": [
    ["iPhone 15 Pro", "$999", "4.5"],
    ["Samsung S24 Ultra", "$1199", "4.7"],
    ["Google Pixel 8", "$699", "4.4"],
    ["OnePlus 12", "$799", "4.3"],
    ["Xiaomi 14", "$649", "4.2"],
    // ... (continue for all 25 smartphones found)
    ["Realme GT 5", "$499", "4.0"]
  ],
  "summary": "Extracted 25 smartphones ranging from $449 to $1199, with ratings between 3.8 and 4.8 stars.",
  "page_info": {{"current_page": 1, "total_pages": 5, "records_extracted": "25"}},
  "outputFormat": "json"
}}

Example 3 - Summarization only:
{{
  "product": "article_content",
  "columns": [],
  "records": [],
  "summary": "The article investigates a critical problem within its field, motivated by limitations observed in 
  existing approaches. It begins by reviewing prior work and identifies performance gaps of approximately 12–18% in 
  accuracy or efficiency across commonly used methods. The authors define the primary objective as improving this 
  performance while maintaining scalability and robustness. To achieve this, the study employs a dataset consisting of
   roughly 50,000 samples, split into 70% for training, 15% for validation, and 15% for testing. The proposed method is 
   evaluated against three baseline models using standardized metrics such as accuracy, precision, recall, and F1-score.
    Experimental results show that the proposed approach achieves an average accuracy of 91.6%, outperforming the best
     baseline by 6.3%. Additionally, inference latency is reduced by nearly 25%, demonstrating improved computational
      efficiency. Statistical significance is validated using confidence intervals at the 95% level and repeated over
       five independent runs. Ablation studies reveal that removing key components leads to a performance drop of up to
        9%, highlighting their importance. The paper also reports a reduction in error variance from 0.042 to 0.019,
         indicating greater model stability. The discussion links these results to theoretical expectations and explains the observed improvements. 
         Limitations are acknowledged, including dataset bias and reduced performance on edge-case inputs, where accuracy 
         drops to around 84%. The authors suggest extending the method to larger datasets and real-world deployments. 
         Overall, the study demonstrates measurable technical improvements and contributes a statistically validated 
         advancement to the field.",
  "page_info": {{"current_page": 1, "total_pages": 1, "records_extracted": "0"}},
  "outputFormat": "markdown"
}}

REMEMBER: Extract EVERY matching item from start to end of content. Do NOT stop early!

NO explanations, NO markdown code blocks, ONLY the raw JSON object!
"""

# ============================================================================
# TASK INSTRUCTION TEMPLATES
# ============================================================================

EXTRACTION_TASK_INSTRUCTIONS = """
1. EXTRACT ALL STRUCTURED DATA:
   - Scan the ENTIRE content from beginning to end
   - Identify EVERY instance of items matching the pattern
   - For each item found, extract: {columns_list}
   - Each record must have exactly {num_columns} values
   - DO NOT stop after finding a few examples - extract EVERYTHING
   - Return all records as list of lists in "records" field
"""

SUMMARIZATION_TASK_INSTRUCTIONS = """
1. ANALYZE AND SUMMARIZE CONTENT:
   - Read and understand the complete content
   - Create a concise 10-11 sentence summary
   - Highlight key information and main points
   - Include relevant statistics if applicable
   - Return in "summary" field
"""

HYBRID_TASK_INSTRUCTIONS = """
1. EXTRACT ALL STRUCTURED DATA:
   - Scan the ENTIRE content from beginning to end
   - Identify EVERY instance of items matching the pattern
   - For each item, extract: {columns_list}
   - DO NOT stop after finding a few examples - extract EVERYTHING

2. CREATE SUMMARY:
   - After extraction, provide 7-8 sentence overview
   - Include statistics: "Extracted X items ranging from Y to Z"
   - Highlight any notable patterns or insights
"""


# ============================================================================
# HELPER FUNCTION
# ============================================================================

def build_extraction_prompt(
        plan: dict,
        cleaned_dom: str,
        current_page: int = 1,
        total_pages: int = 1
) -> str:
    """
    Builds the extraction prompt based on the scrape plan.

    Args:
        plan: Dict with task_type, columns, include_summary, output_format
        cleaned_dom: Cleaned text content from Trafilatura
        current_page: Current page number
        total_pages: Total pages being scraped

    Returns:
        Formatted prompt string
    """
    task_type = plan.get('task_type', 'structured_extraction')
    columns = plan.get('columns', [])
    include_summary = plan.get('include_summary', False)
    output_format = plan.get('output_format', 'json')

    # Determine task instructions
    if task_type == 'structured_extraction':
        task_instructions = EXTRACTION_TASK_INSTRUCTIONS.format(
            columns_list=', '.join(columns),
            num_columns=len(columns)
        )
    elif task_type == 'summarization':
        task_instructions = SUMMARIZATION_TASK_INSTRUCTIONS
    else:  # hybrid
        task_instructions = HYBRID_TASK_INSTRUCTIONS.format(
            columns_list=', '.join(columns)
        )

    # Summary value placeholder
    summary_value = '"Your summary here"' if include_summary or task_type in ['summarization', 'hybrid'] else 'null'

    # Build final prompt
    return CLEANED_DOM_EXTRACTION_PROMPT.format(
        task_type=task_type,
        columns=columns,
        include_summary=include_summary,
        output_format=output_format,
        cleaned_dom=cleaned_dom,
        current_page=current_page,
        total_pages=total_pages,
        task_instructions=task_instructions.strip(),
        summary_value=summary_value,
        num_columns=len(columns) if columns else 0
    )