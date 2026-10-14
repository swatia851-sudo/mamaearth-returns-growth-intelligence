
import os
import json
import time
import random
from datetime import datetime
from google import genai
from google.genai import types


def generate_scr_narrative_offline(findings: dict) -> dict:
    """
    Fully offline fallback.
    No API key or network connection is required.
    """

    cleaned = findings["cleaned_total_revenue_inr"]
    raw = findings["raw_total_revenue_inr"]
    delta = findings["duplicate_reconciliation_delta_inr"]

    cod_rate = findings["return_rate_by_payment"]["COD"]

    risk = findings["highest_risk_segment"]
    risk_rate = risk["return_rate_pct"]

    peak = findings["true_peak_month"]
    peak_revenue = peak["revenue_inr"]

    peak_date = datetime.strptime(peak["month"], "%Y-%m")
    peak_month_name = peak_date.strftime("%B %Y")

    narrative = f"""
Situation

Mamaearth's cleaned total revenue is ₹{cleaned:,.2f}, compared with a raw
total revenue of ₹{raw:,.2f}. The payment-method analysis shows that COD
has a return rate of {cod_rate:.1f}%.

Complication

The highest-risk segment is {risk["payment_method"]} in Tier-{risk["city_tier"]}
cities, with a return rate of {risk_rate:.1f}%. The reconciliation analysis
also shows a difference of ₹{delta:,.2f}, caused by the five duplicate orders
removed during cleaning.

Resolution

After correcting the data and excluding the quantity outliers, {peak_month_name}
is the true peak month, with revenue of ₹{peak_revenue:,.2f}. These
verified figures can be used by the regional operations and finance teams
for further analysis.
""".strip()

    return {
        "status": "success",
        "narrative": narrative,
        "tokens": 0
    }


def call_gemini_scr(findings: dict) -> dict:
    """Call Gemini and return either a success or error dictionary."""

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "narrative": None,
            "message": "GEMINI_API_KEY is not configured."
        }

    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=60000)
        )

        system_instruction = """
You are a senior data analyst writing for Mamaearth's regional ops
and finance heads.

Write the business narrative using exactly three labeled sections:
Situation
Complication
Resolution

Every number in the output must come only from the supplied findings.
Do not invent statistics, percentages, revenues, counts, or other numbers.
Use the supplied values exactly, allowing only normal display formatting.
When referring to the month "2026-03", write it as "March 2026".
"""

        user_prompt = f"""
Create an SCR business narrative from these verified findings:

{json.dumps(findings, indent=2)}
"""

        response = None

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.0,
                        max_output_tokens=500
                    )
                )
                break
            except Exception:
                if attempt == 2:
                    raise
                wait_seconds = (2 ** attempt) + random.random()
                print(f"Gemini request failed; retrying in {wait_seconds:.1f} seconds...")
                time.sleep(wait_seconds)

        narrative = (response.text or "").strip()

        if not narrative:
            raise ValueError("Gemini returned an empty narrative.")

        if not all(
            section in narrative
            for section in ["Situation", "Complication", "Resolution"]
        ):
            raise ValueError("Gemini returned an incomplete SCR narrative.")

        if not check_numeric_accuracy(narrative, verbose=False):
            raise ValueError("Gemini narrative failed numeric accuracy checks.")

        tokens = 0

        if getattr(response, "usage_metadata", None):
            tokens = getattr(
                response.usage_metadata,
                "total_token_count",
                0
            ) or 0

        return {
            "status": "success",
            "narrative": narrative,
            "tokens": tokens
        }

    except Exception as err:
        return {
            "status": "error",
            "narrative": None,
            "message": str(err)
        }


def generate_scr_narrative(findings: dict) -> dict:
    """
    Generate an SCR narrative using Gemini.
    If Gemini fails, use the offline fallback and include the error message.
    """

    gemini_result = call_gemini_scr(findings)

    if gemini_result["status"] == "error":
        offline_result = generate_scr_narrative_offline(findings)
        offline_result["status"] = "offline_fallback"
        offline_result["message"] = gemini_result["message"]
        return offline_result

    return gemini_result


def check_numeric_accuracy(narrative: str, verbose: bool = True) -> bool:
    """
    Check the five required figures from the assessment.
    """

    normalized = narrative.replace(",", "")

    checks = {
        "Cleaned revenue 97358.30":
            "97358.30" in normalized or "97358.3" in normalized,

        "COD return rate 44.4":
            "44.4" in normalized,

        "Highest-risk segment 54.5":
            "54.5" in normalized,

        "Duplicate delta 2501.90":
            "2501.90" in normalized or "2501.9" in normalized,

        "March peak revenue 20318.90":
            "March" in narrative and
            ("20318.90" in normalized or "20318.9" in normalized)
    }

    overall = all(checks.values())

    if verbose:
        print("Numeric accuracy check:")
        for name, passed in checks.items():
            print(f"{'PASS' if passed else 'FAIL'}: {name}")
        print(f"\nOverall result: {'PASS' if overall else 'FAIL'}")

    return overall


if __name__ == "__main__":
    with open("narrator/findings.json", "r", encoding="utf-8") as f:
        findings = json.load(f)

    result = generate_scr_narrative(findings)

    print("===== MAMAEARTH SCR NARRATIVE =====")
    print(result["narrative"])

    print("\n===== NUMERIC ACCURACY CHECK =====")
    check_numeric_accuracy(result["narrative"])
