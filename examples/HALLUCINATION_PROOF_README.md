# Hallucination-Proof Data Extractor Example

This example demonstrates how to prevent LLM hallucinations in data extraction tasks using validation and self-optimization.

## What is Hallucination?

In the context of Large Language Models (LLMs), **hallucination** refers to when the model generates information that:
- Is not present in the source material
- Is factually incorrect
- Is fabricated or invented by the model

This is a critical issue in data extraction tasks where accuracy is paramount.

## How This Example Works

### 1. **Grounding Validation**

The `GroundingValidator` checks that every extracted value actually exists in the source document:

```python
class GroundingValidator(CustomValidator):
    def validate_grounding(self, output: str, context: Optional[Dict[str, Any]] = None):
        # Parse extracted JSON
        data = json.loads(output)
        
        # Check each value against source text
        for field, value in data.items():
            if not self._check_value_in_source(value):
                # Flag as hallucination
                hallucinations.append(field)
```

### 2. **Detection Strategy**

The validator uses multiple techniques to verify values:

- **Direct text matching**: Case-insensitive search for text values
- **Numeric validation**: Handles different number formats ($249.99 vs 249.99)
- **Phone number handling**: Recognizes different phone formats
- **Date flexibility**: Accounts for various date representations

### 3. **Automatic Learning**

When hallucinations are detected:

1. The validator flags the specific fields with fabricated data
2. The critic model analyzes the failure
3. Instructions are updated to improve literal fidelity
4. The system retries with improved guidance

### 4. **Learning Cycle**

```
Extract Data → Validate → Hallucination Detected
      ↑                            ↓
  Retry with              Update Instructions
  Better Instructions      (Emphasize Grounding)
      ↑____________________________↓
```

## Running the Example

### Basic Usage

```bash
python examples/hallucination_proof_extractor.py
```

### With Real API Keys

For better results with actual LLMs, set up your API keys:

```bash
# .env file
OPENAI_API_KEY=your_key_here
# or
ANTHROPIC_API_KEY=your_key_here
```

Then the example will use real models that can demonstrate actual hallucination detection and correction.

## Key Components

### Source Document

The example uses a messy invoice as test data:

```
INVOICE #4582-2024
Date: March 15th, 2024
Customer Info:
Name: John Smith
...
```

### Expected Extractions

The system should extract:
- Invoice number
- Date
- Customer information (name, email, phone)
- Order details (items, prices, quantities)
- Payment and shipping information

### Grounding Validator

Custom validator that ensures:
- ✅ Every extracted value exists in source
- ✅ No fabricated or assumed data
- ✅ Accurate representation of source content

## Real-World Applications

This pattern is critical for:

### 1. **Invoice/Receipt Processing**
- Extract payment information
- Verify line items and totals
- Ensure accurate tax calculations

### 2. **Medical Record Extraction**
- Patient information must be exact
- Medication dosages cannot be assumed
- Dates and times must be precise

### 3. **Legal Document Analysis**
- Contract terms must be quoted exactly
- Dates and parties must be verified
- No interpretation or inference

### 4. **Financial Document Processing**
- Account numbers must be exact
- Monetary amounts must match source
- Transaction details must be grounded

### 5. **Compliance and Audit**
- Regulatory information must be accurate
- No fabricated compliance data
- Traceable to source documents

## Customization

### Adding More Validators

You can add additional validators alongside grounding validation:

```python
from src import JSONValidator, LengthValidator

system.add_validator(GroundingValidator(source_text))
system.add_validator(JSONValidator(required_fields=["invoice_number", "total_amount"]))
system.add_validator(LengthValidator(max_length=5000))
```

### Adjusting Validation Strictness

Modify the `GroundingValidator` to be more or less strict:

```python
# More strict: exact matches only
def _check_text_in_source(self, value_str: str) -> bool:
    return value_str in self.source_text  # Exact, case-sensitive

# Less strict: allow partial matches
def _check_text_in_source(self, value_str: str) -> bool:
    words = value_str.split()
    return all(word.lower() in self.source_text.lower() for word in words)
```

### Different Document Types

Adapt the example for different document types:

```python
# For structured forms
MESSY_DOCUMENT = """
[Your form content here]
"""

# For emails
MESSY_DOCUMENT = """
From: user@example.com
To: recipient@example.com
Subject: Important Information
[Email body]
"""

# For reports
MESSY_DOCUMENT = """
Q4 2023 Financial Report
Revenue: $1.2M
Expenses: $800K
...
"""
```

## Performance Tips

### 1. **Use Lower Temperature**
For extraction tasks, use lower temperature values:
```python
config = SystemConfig(
    temperature_main=0.1,  # More deterministic
    temperature_critic=0.2,
)
```

### 2. **Provide Clear Instructions**
Be explicit about not inventing data:
```python
prompt = """
Extract data from the document.
IMPORTANT: Only extract values that are explicitly present in the source.
Do not infer, assume, or calculate any values.
If a value is not present, use null.
"""
```

### 3. **Use Structured Output**
Request specific JSON schemas:
```python
prompt = """
Return JSON with exactly these fields:
{
  "invoice_number": "string or null",
  "date": "string or null",
  ...
}
"""
```

## Troubleshooting

### Issue: Too Many False Positives

If the validator flags valid extractions as hallucinations:
- Check for format mismatches (e.g., "$100" vs "100.00")
- Add more flexible matching logic
- Normalize values before comparison

### Issue: Missing Hallucinations

If the validator misses actual hallucinations:
- Increase strictness of matching
- Add domain-specific validation rules
- Check for inference vs. extraction

### Issue: Slow Performance

With real API calls:
- Use faster models for initial attempts
- Cache source text analysis
- Batch multiple extractions

## Further Reading

- [Understanding LLM Hallucinations](https://en.wikipedia.org/wiki/Hallucination_(artificial_intelligence))
- [Grounding in Natural Language Processing](https://aclanthology.org/)
- [Validation Strategies for ML Systems](https://developers.google.com/machine-learning/testing-debugging/pipeline/deploying)

## Contributing

Have improvements for this example? We welcome:
- Better validation heuristics
- Support for more document types
- Enhanced hallucination detection
- Performance optimizations

Submit a PR or open an issue on GitHub!
