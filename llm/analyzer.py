"""
Main LLM analyzer with self-healing retry loop and full prompt integration
"""

import json
import sys
from .client import invoke_llm
from .prompts import (
    SCRAPE_PLAN_PROMPT,
    CLEANED_DOM_EXTRACTION_PROMPT,
    EXTRACTION_TASK_INSTRUCTIONS,
    SUMMARIZATION_TASK_INSTRUCTIONS,
    HYBRID_TASK_INSTRUCTIONS,
    build_extraction_prompt
)
from .utils import safe_json_loads
from .validator import validate_extraction, format_retry_prompt


def plan_scraping(url, user_request):
    """
    Stage 1: Create scraping plan from user request using LLM

    Args:
        url: str - Target URL
        user_request: str - Natural language description of what to scrape

    Returns:
        dict: Scraping plan with URL, pages, task_type, columns, etc.
    """
    print(f"📋 Planning scrape...", file=sys.stderr)
    print(f"   URL: {url}", file=sys.stderr)
    print(f"   Request: {user_request}", file=sys.stderr)

    # Build planning prompt
    prompt = SCRAPE_PLAN_PROMPT.format(
        url=url,
        request=user_request
    )

    # Call LLM
    response = invoke_llm(prompt)

    if not response:
        print(f"❌ LLM returned no response for planning", file=sys.stderr)
        # Return default plan
        return {
            "URL": url,
            "pages": 1,
            "task_type": "structured_extraction",
            "columns": [],
            "include_summary": False,
            "output_format": "json"
        }

    try:
        plan = safe_json_loads(response)

        print(type(plan))

        """
        # Validate plan structure
        plan.setdefault("URL", url)
        plan.setdefault("pages", 1)
        plan.setdefault("task_type", "structured_extraction")
        plan.setdefault("columns", [])
        plan.setdefault("include_summary", False)
        plan.setdefault("output_format", "json")
        """

        print(f"✅ Plan created:", file=sys.stderr)
        print(f"   Task type: {plan['task_type']}", file=sys.stderr)
        print(f"   Columns: {plan['columns']}", file=sys.stderr)
        print(f"   Format: {plan['output_format']}", file=sys.stderr)

        return plan

    except Exception as e:
        print(f"❌ Failed to parse plan: {e}", file=sys.stderr)
        print(f"   Response was: {response[:200]}...", file=sys.stderr)

        # Return default plan
        return {
            "URL": url,
            "pages": 1,
            "task_type": "structured_extraction",
            "columns": [],
            "include_summary": False,
            "output_format": "json"
        }


def analyze_cleaned_dom(
        cleaned_dom,
        plan=None,
        columns=None,
        output_format="json",
        current_page=1,
        total_pages=1,
        max_retries=3
):
    """
    Stage 2: Analyze cleaned DOM with self-healing retry loop

    Args:
        cleaned_dom: str - Trafilatura output
        plan: dict - Scraping plan from plan_scraping() (optional)
        columns: list - Columns to extract (used if plan is None)
        output_format: str - Output format (used if plan is None)
        current_page: int - Current page number
        total_pages: int - Total pages being scraped
        max_retries: int - Maximum retry attempts

    Returns:
        dict: Validated extraction result
    """

    # If plan is provided, use it; otherwise use legacy parameters
    if plan:
        task_type = plan.get('task_type')
        columns = plan.get('columns')
        include_summary = plan.get('include_summary', False)
        output_format = plan.get('output_format', 'json')
    else:
        # Legacy mode: structured extraction only
        task_type = 'structured_extraction'
        include_summary = False
        columns = columns or []

        # Wrap in plan structure for consistency
        plan = {
            'task_type': task_type,
            'columns': columns,
            'include_summary': include_summary,
            'output_format': output_format
        }

    print(f"📊 Analyzing cleaned DOM...", file=sys.stderr)
    print(f"   Content length: {len(cleaned_dom)} chars", file=sys.stderr)
    print(f"   Task type: {task_type}", file=sys.stderr)
    print(f"   Columns: {columns}", file=sys.stderr)
    print(f"   Page: {current_page}/{total_pages}", file=sys.stderr)
    print(f"   Max retries: {max_retries}", file=sys.stderr)

    # Limit content size to avoid token limits
    """
    max_content_length = 15000  # Adjust based on your LLM's context window
    if len(cleaned_dom) > max_content_length:
        cleaned_dom = cleaned_dom[:max_content_length]
        print(f"   ✂️ Truncated to {max_content_length} chars", file=sys.stderr)
    """

    # Keep sample for validation
    cleaned_dom_sample = cleaned_dom[:1000]

    # Build initial prompt using the new system
    prompt = build_extraction_prompt(
        plan=plan,
        cleaned_dom=cleaned_dom,
        current_page=current_page,
        total_pages=total_pages
    )

    # Retry loop with self-healing
    for attempt in range(max_retries):
        print(f"\n🔄 Attempt {attempt + 1}/{max_retries}", file=sys.stderr)

        # Call LLM
        response = invoke_llm(prompt)

        if not response:
            print(f"❌ LLM returned no response", file=sys.stderr)
            if attempt < max_retries - 1:
                print(f"   Retrying...", file=sys.stderr)
                continue
            else:
                return create_fallback_payload(
                    task_type, columns, output_format,
                    current_page, total_pages
                )

        # Parse response
        try:
            print(f"🔍 Parsing LLM output...", file=sys.stderr)
            result = safe_json_loads(response)

            # Ensure basic structure
            result.setdefault("product", "scraped_data")
            result.setdefault("columns", columns)
            result.setdefault("records", [])
            result.setdefault("summary", None)
            result.setdefault("outputFormat", output_format)
            result.setdefault("page_info", {
                "current_page": current_page,
                "total_pages": total_pages,
                "records_extracted": 0
            })

            # Validate records structure
            if not isinstance(result["records"], list):
                result["records"] = []

            # Filter valid records (only for structured extraction)
            if task_type in ['structured_extraction', 'hybrid']:
                valid_records = []
                for record in result["records"]:
                    if isinstance(record, list) and len(record) == len(columns):
                        valid_records.append(record)
                    else:
                        print(f"   ⚠️ Skipping invalid record: {record}", file=sys.stderr)

                result["records"] = valid_records
                result["page_info"]["records_extracted"] = len(valid_records)
            else:
                # Summarization mode - no records expected
                result["records"] = []
                result["page_info"]["records_extracted"] = 0

            print(f"✅ Parsed: {len(result['records'])} records", file=sys.stderr)
            if result.get("summary"):
                print(f"✅ Summary generated: {len(result['summary'])} chars", file=sys.stderr)

            if (task_type in ['structured_extraction', 'hybrid']):
                # VALIDATE RESULT
                is_valid, feedback = validate_extraction(
                    result,
                    columns,
                    cleaned_dom_sample,
                    task_type
                )

                if is_valid:
                    print(f"✅ VALIDATION PASSED", file=sys.stderr)
                    print(f"   Product: {result['product']}", file=sys.stderr)
                    print(f"   Records: {len(result['records'])}", file=sys.stderr)
                    if result.get("summary"):
                        print(f"   Summary: Yes ({len(result['summary'])} chars)", file=sys.stderr)
                    return result
                else:
                    print(f"⚠️ VALIDATION FAILED", file=sys.stderr)
                    print(f"   Feedback: {feedback}", file=sys.stderr)

                    if attempt < max_retries - 1:
                        print(f"   🔄 Preparing retry with feedback...", file=sys.stderr)

                        # Generate retry prompt with feedback
                        retry_base = build_extraction_prompt(
                            plan=plan,
                            cleaned_dom=cleaned_dom,
                            current_page=current_page,
                            total_pages=total_pages
                        )

                        prompt = format_retry_prompt(
                            retry_base,
                            feedback,
                            json.dumps(result, indent=2)
                        )
                    else:
                        print(f"   ❌ Max retries reached, using best attempt", file=sys.stderr)
                        return result
            else:
                return result
        except Exception as e:
            print(f"❌ Parse error: {e}", file=sys.stderr)
            print(f"   Response preview: {response[:300]}...", file=sys.stderr)

            if attempt < max_retries - 1:
                print(f"   Retrying...", file=sys.stderr)
                continue
            else:
                return create_fallback_payload(
                    task_type, columns, output_format,
                    current_page, total_pages
                )

    # Should not reach here, but fallback just in case
    return create_fallback_payload(
        task_type, columns, output_format,
        current_page, total_pages
    )


def create_fallback_payload(task_type, columns, output_format, current_page=1, total_pages=1):
    """Create fallback payload when all retries fail"""
    print(f"🔄 Using fallback payload", file=sys.stderr)

    payload = {
        "product": "scraped_data",
        "columns": columns,
        "records": [],
        "outputFormat": output_format,
        "page_info": {
            "current_page": current_page,
            "total_pages": total_pages,
            "records_extracted": 0
        }
    }

    # Add summary field if needed
    if task_type in ['summarization', 'hybrid']:
        payload["summary"] = "Failed to extract content after multiple attempts."
    else:
        payload["summary"] = None

    return payload


def analyze_multi_page(cleaned_pages, plan, max_retries=3):
    """
    Analyze multiple pages and combine results

    Args:
        cleaned_pages: list of str - Cleaned content from each page
        plan: dict - Scraping plan
        max_retries: int - Max retries per page

    Returns:
        dict: Combined extraction result from all pages
    """
    total_pages = len(cleaned_pages)
    task_type = plan.get('task_type', 'structured_extraction')
    columns = plan.get('columns', [])
    output_format = plan.get('output_format', 'json')

    print(f"\n📚 Analyzing {total_pages} pages...", file=sys.stderr)

    all_records = []
    all_summaries = []

    for i, page_content in enumerate(cleaned_pages, start=1):
        print(f"\n{'=' * 60}", file=sys.stderr)
        print(f"📄 Processing page {i}/{total_pages}", file=sys.stderr)
        print(f"{'=' * 60}", file=sys.stderr)

        result = analyze_cleaned_dom(
            cleaned_dom=page_content,
            plan=plan,
            current_page=i,
            total_pages=total_pages,
            max_retries=max_retries
        )

        # Collect records
        if result.get("records"):
            all_records.extend(result["records"])
            print(f"   ✅ Extracted {len(result['records'])} records from page {i}", file=sys.stderr)

        # Collect summaries
        if result.get("summary"):
            all_summaries.append(f"Page {i}: {result['summary']}")

    # Combine results
    combined_result = {
        "product": plan.get('columns', ['data'])[0] if columns else "scraped_data",
        "columns": columns,
        "records": all_records,
        "outputFormat": output_format,
        "page_info": {
            "current_page": total_pages,
            "total_pages": total_pages,
            "records_extracted": len(all_records)
        }
    }

    # Add combined summary if needed
    if task_type in ['summarization', 'hybrid']:
        if all_summaries:
            combined_result["summary"] = "\n\n".join(all_summaries)
        else:
            combined_result["summary"] = f"Processed {total_pages} pages, extracted {len(all_records)} total records."
    else:
        combined_result["summary"] = None

    print(f"\n{'=' * 60}", file=sys.stderr)
    print(f"✅ FINAL RESULTS", file=sys.stderr)
    print(f"{'=' * 60}", file=sys.stderr)
    print(f"   Total records: {len(all_records)}", file=sys.stderr)
    print(f"   Pages processed: {total_pages}", file=sys.stderr)
    if combined_result.get("summary"):
        print(f"   Summary: Generated", file=sys.stderr)

    return combined_result