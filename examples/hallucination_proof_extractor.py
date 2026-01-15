#!/usr/bin/env python3
"""
Hallucination-Proof Data Extractor Example

Demonstrates an agent extracting data from messy, unstructured text with validation
to ensure that every extracted value actually exists in the source text.

This example showcases:
1. Data extraction from messy documents
2. Validator that checks for hallucinations (invented values)
3. Self-optimization when hallucinations are detected
4. Learning cycle: fail → analyze → update instructions
"""

import sys
import os
import json
import re
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import SelfOptimizingSystem, SystemConfig, CustomValidator
from src.core.validator import ValidationResult


# Constants for validation
MIN_WORD_LENGTH_FOR_MATCHING = (
    2  # Minimum word length to consider in multi-word validation
)
PHONE_MIN_DIGITS = 10  # Minimum number of digits for a valid phone number
PHONE_MAX_DIGITS = 15  # Maximum number of digits for a valid phone number


# Sample messy document for extraction
MESSY_DOCUMENT = """
INVOICE #4582-2024
Date: March 15th, 2024

Customer Info:
Name: John Smith
Email: j.smith@example.com
Phone: (555) 123-4567

Order Details:
- Widget Pro Model X: $249.99 (qty: 2)
- Shipping & Handling: $15.50
- Tax (8.5%): $43.82
TOTAL: $559.30

Payment Method: Credit Card ending in 8742
Order Status: SHIPPED on 03/18/2024
Tracking: TRK-9384756ABC

Notes: Customer requested gift wrapping (+$5.00)
Delivery address verified. Expected delivery: March 22, 2024
"""


class GroundingValidator(CustomValidator):
    """
    Validator that checks if extracted data is grounded in the source text.
    Prevents hallucinations by verifying each extracted value exists in the source.
    """

    def __init__(self, source_text: str):
        self.source_text = source_text
        super().__init__("GroundingValidator", self.validate_grounding)

    def validate_grounding(
        self, output: str, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate that all extracted values actually exist in the source text.
        """
        try:
            # Try to parse as JSON
            data = json.loads(output)
        except json.JSONDecodeError:
            return ValidationResult(
                passed=False,
                validator_name=self.name,
                error_message="Output is not valid JSON",
                error_details={"error": "Could not parse JSON"},
            )

        hallucinations = []
        verified_fields = []

        # Check each extracted field
        for field, value in data.items():
            if value is None or value == "":
                continue

            # Convert value to string for checking
            value_str = str(value)

            # For numeric values, be more flexible (allow for formatting differences)
            if self._is_numeric(value_str):
                if not self._check_numeric_in_source(value_str):
                    hallucinations.append(
                        {
                            "field": field,
                            "value": value_str,
                            "reason": "Numeric value not found in source",
                        }
                    )
                else:
                    verified_fields.append(field)
            else:
                # For text values, check if it appears in source (case-insensitive)
                # Also handle partial matches and common variations
                if not self._check_text_in_source(value_str):
                    hallucinations.append(
                        {
                            "field": field,
                            "value": value_str,
                            "reason": "Text value not found in source",
                        }
                    )
                else:
                    verified_fields.append(field)

        if hallucinations:
            return ValidationResult(
                passed=False,
                validator_name=self.name,
                error_message=f"Found {len(hallucinations)} hallucinated value(s): {', '.join([h['field'] for h in hallucinations])}",
                error_details={
                    "hallucinations": hallucinations,
                    "verified_fields": verified_fields,
                    "total_fields": len(data),
                },
            )

        return ValidationResult(
            passed=True,
            validator_name=self.name,
            error_message=None,
            error_details={
                "verified_fields": verified_fields,
                "total_fields": len(data),
            },
        )

    def _is_numeric(self, value_str: str) -> bool:
        """Check if a string represents a numeric value."""
        # Remove common formatting characters
        cleaned = value_str.replace("$", "").replace(",", "").replace("%", "").strip()
        try:
            float(cleaned)
            return True
        except ValueError:
            return False

    def _check_numeric_in_source(self, value_str: str) -> bool:
        """Check if a numeric value exists in source (allowing for format variations)."""
        # Extract the numeric part
        cleaned = value_str.replace("$", "").replace(",", "").replace("%", "").strip()
        try:
            num = float(cleaned)
        except ValueError:
            return False

        # Check various formats of the number
        patterns = [
            str(num),
            f"{num:.2f}",
            f"${num:.2f}",
            f"${num:,.2f}",
            str(int(num)) if isinstance(num, float) and num.is_integer() else None,
        ]

        for pattern in patterns:
            if pattern and pattern in self.source_text:
                return True

        return False

    def _check_text_in_source(self, value_str: str) -> bool:
        """Check if text value exists in source (case-insensitive, flexible)."""
        # Clean the value
        value_clean = value_str.strip()

        # Direct match (case-insensitive)
        if value_clean.lower() in self.source_text.lower():
            return True

        # Check if it's a partial match or reformatted version
        # For dates, phone numbers, etc.
        words = value_clean.split()
        if len(words) > 1:
            # For multi-word values, check if all significant words appear
            all_words_found = all(
                word.lower() in self.source_text.lower()
                for word in words
                if len(word) > MIN_WORD_LENGTH_FOR_MATCHING
            )
            if all_words_found:
                return True

        # Check for phone number variations with proper constraints
        # Match strings that look like phone numbers: contain mostly digits and phone formatting chars
        if re.match(r"^[\d\(\)\-\s\.]+$", value_clean):
            # Extract just digits
            digits = re.sub(r"\D", "", value_clean)
            # Validate digit count is within reasonable phone number range
            if PHONE_MIN_DIGITS <= len(digits) <= PHONE_MAX_DIGITS:
                source_digits = re.sub(r"\D", "", self.source_text)
                if digits in source_digits:
                    return True

        return False


def main():
    """Demonstrate hallucination-proof data extraction"""

    print("=" * 70)
    print("HALLUCINATION-PROOF DATA EXTRACTOR EXAMPLE")
    print("=" * 70)
    print()

    print("This example demonstrates:")
    print("  1. Extracting structured data from messy, unstructured text")
    print("  2. Validating that extracted values are grounded in source")
    print("  3. Self-optimization when hallucinations are detected")
    print("  4. Learning cycle to improve literal fidelity")
    print()
    print("-" * 70)

    # Display the source document
    print("\n📄 SOURCE DOCUMENT:")
    print("-" * 70)
    print(MESSY_DOCUMENT)
    print("-" * 70)

    # Initialize the system with specific configuration
    config = SystemConfig(
        main_model="gpt-4o-mini",  # Using a specific model
        main_model_provider="openai",
        critic_model="gpt-4o-mini",
        critic_model_provider="openai",
        enable_auto_optimization=True,
        max_optimization_attempts=3,
        temperature_main=0.3,  # Lower temperature for more factual extraction
    )

    system = SelfOptimizingSystem(config)

    # Add the grounding validator
    grounding_validator = GroundingValidator(MESSY_DOCUMENT)
    system.add_validator(grounding_validator)

    print("\n✅ System initialized with GroundingValidator")
    print("   This validator checks that all extracted values exist in the source text")

    # Define the extraction task
    extraction_prompt = f"""
Extract the following information from the document and return it as JSON:
- invoice_number
- date
- customer_name
- customer_email
- customer_phone
- item_name
- item_price
- quantity
- shipping
- tax
- total_amount
- payment_method
- tracking_number
- order_status

Document:
{MESSY_DOCUMENT}

Return ONLY valid JSON with the extracted data. Do not include any explanatory text.
"""

    print("\n🔍 EXTRACTION TASK:")
    print("   Extracting: invoice_number, customer details, order details, etc.")
    print()

    # Attempt 1: Initial extraction (may hallucinate)
    print("-" * 70)
    print("ATTEMPT 1: Initial Extraction")
    print("-" * 70)

    result1 = system.execute(extraction_prompt)

    print("\n📤 Extracted Data:")
    try:
        data = json.loads(result1["output"])
        for key, value in data.items():
            print(f"   {key}: {value}")
    except json.JSONDecodeError:
        print(f"   {result1['output'][:200]}...")

    print(f"\n✓ Validation Passed: {result1['validation_passed']}")

    if not result1["validation_passed"]:
        print("\n⚠️  HALLUCINATIONS DETECTED!")

        # Show validation errors
        for val_result in result1.get("validation_results", []):
            if not val_result.passed and val_result.error_details:
                details = val_result.error_details
                if "hallucinations" in details:
                    print(f"\n   Hallucinated fields:")
                    for h in details["hallucinations"]:
                        print(f"     - {h['field']}: '{h['value']}'")
                        print(f"       Reason: {h['reason']}")

        if result1.get("optimization_attempted"):
            opt_result = result1["optimization_result"]
            print(
                f"\n🔄 Auto-optimization triggered: {opt_result.get('success', False)}"
            )
            if opt_result.get("success"):
                print("   ✓ Instructions updated to improve grounding!")
                print(f"   Changes: {opt_result.get('diff_summary', 'N/A')}")

    else:
        print("\n✅ All extracted values are grounded in the source text!")

    # If optimization occurred, try again
    if result1.get("optimization_attempted") and result1["optimization_result"].get(
        "success"
    ):
        print("\n" + "=" * 70)
        print("ATTEMPT 2: Re-extraction with Optimized Instructions")
        print("=" * 70)

        result2 = system.execute(extraction_prompt)

        print("\n📤 Extracted Data:")
        try:
            data = json.loads(result2["output"])
            for key, value in data.items():
                print(f"   {key}: {value}")
        except json.JSONDecodeError:
            print(f"   {result2['output'][:200]}...")

        print(f"\n✓ Validation Passed: {result2['validation_passed']}")

        if result2["validation_passed"]:
            print("\n🎉 SUCCESS! All data is now properly grounded!")
        else:
            print("\n⚠️  Still detecting issues. Further optimization may be needed.")

            if result2.get("optimization_attempted"):
                opt_result = result2["optimization_result"]
                if opt_result.get("success"):
                    print("   ✓ Instructions updated again")

    # Show version history
    print("\n" + "=" * 70)
    print("📚 VERSION HISTORY")
    print("=" * 70)

    history = system.get_version_history()
    if history:
        for i, version in enumerate(history[-3:], 1):
            print(f"\n{i}. {version['version_id']}")
            print(f"   Trigger: {version['trigger_type']}")
            print(f"   Changes: {version['diff_summary']}")
    else:
        print("No version history available (using mock models)")

    # Summary
    print("\n" + "=" * 70)
    print("💡 KEY TAKEAWAYS")
    print("=" * 70)
    print(
        """
This example demonstrates:

1. **Grounding Validation**: Every extracted value is checked against the source
   text to prevent hallucinations (invented data).

2. **Automatic Learning**: When hallucinations are detected, the system
   automatically updates its instructions to improve literal fidelity.

3. **Iterative Improvement**: The system learns from failures, getting better
   at extracting only verified data.

4. **Real-world Application**: This pattern is crucial for:
   - Invoice/receipt processing
   - Document data extraction
   - Medical record parsing
   - Legal document analysis
   - Any scenario where accuracy is critical

5. **Prevention Strategy**: The validator enforces that LLMs must:
   - Quote directly from source
   - Not infer or assume values
   - Only extract what's explicitly present
"""
    )

    print("\n" + "=" * 70)
    print("Example Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
