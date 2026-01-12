# Self-Healing Code Assistant Example

## Overview

This example demonstrates an AI-powered code assistant that generates Python scripts and automatically improves its own code generation quality through validation and self-optimization.

**The Problem:** LLMs can generate code that looks reasonable but contains syntax errors, style violations, or doesn't follow best practices. Manual review is time-consuming and error-prone.

**The Solution:** A self-healing code assistant that:
1. Generates Python code based on user requests
2. Validates syntax using Python's AST parser
3. Checks for style issues (indentation, docstrings, line length, etc.)
4. Automatically learns from failures to improve future code generation
5. Iteratively refines its approach until code meets quality standards

## Why This Is Valuable

### Real-World Need
- **Users want code that runs**: Generated code must be syntactically valid
- **Consistency matters**: Code should follow style guidelines and best practices
- **Time savings**: Automated validation catches issues before manual review
- **Reliability**: Self-optimization improves success rates over time

### Business Value
- **Developer productivity**: Faster prototyping and scaffolding
- **Quality assurance**: Automated enforcement of coding standards
- **Cost reduction**: Less time debugging AI-generated code
- **LLMOps best practices**: Demonstrates production-ready AI code generation

### Technical Innovation
- **Automated feedback loop**: System learns from its own mistakes
- **Multi-layered validation**: Syntax + style checking
- **Iterative improvement**: Gets better with each failure
- **Enterprise-ready**: Scales to production code generation workflows

## How It Works

### Architecture

```
User Request → Code Generation → Validation → Self-Healing Loop
                                    ↓              ↓
                              [Syntax Check]  [Update Instructions]
                              [Style Check]        ↓
                                    ↓         [Retry Generation]
                              Pass/Fail → Better Code Next Time
```

### Validation Layers

1. **Syntax Validation** (Critical)
   - Uses Python's `ast.parse()` to verify code compiles
   - Catches syntax errors before execution
   - Provides line numbers and error details

2. **Style Validation** (Quality)
   - No tabs (use spaces for indentation)
   - Functions must have docstrings
   - Line length limits (120 characters)
   - No bare `except:` clauses (must specify exception types)

3. **Self-Optimization** (Learning)
   - Analyzes validation failures
   - Updates code generation instructions
   - Learns patterns to avoid future mistakes
   - Tracks improvement over time

## Features

### ✅ Syntax Checking
- Validates Python code syntax using AST parser
- Catches errors before code execution
- Provides detailed error messages with line numbers

### ✅ Style Enforcement
- **Indentation**: Enforces spaces over tabs
- **Documentation**: Requires function docstrings
- **Readability**: Limits line length for maintainability
- **Error Handling**: Discourages bare except clauses

### ✅ Self-Healing
- Automatically detects code quality issues
- Updates instructions to prevent similar failures
- Learns coding patterns and best practices
- Improves success rate over time

### ✅ Iterative Improvement
- Each failure becomes a learning opportunity
- System gets progressively better at code generation
- Version history tracks improvements
- Rollback capability for testing

## Usage

### Basic Usage

```bash
# Run the example
python examples/self_healing_code_assistant.py
```

### Example Output

```
🛠️  SELF-HEALING CODE ASSISTANT DEMO
======================================================================

🧑‍💻 CODE GENERATION TEST - Attempt #1
======================================================================

Task: Simple Calculator Function
Category: basic

📝 Request:
   "Write a Python function called 'add_numbers' that takes two parameters and returns their sum."

🤖 Generated Code:
----------------------------------------------------------------------
def add_numbers(a, b):
    """Add two numbers and return the sum."""
    return a + b
----------------------------------------------------------------------

✅ CODE VALIDATION: PASSED
   The generated code is syntactically valid and follows style guidelines!
   ✓ Code lines: 3
   ✓ Status: Valid
```

### With Validation Failures

```
❌ CODE VALIDATION: FAILED
   ⚠️  CODE QUALITY ISSUES DETECTED!

   Found 2 issue(s):
   1. [MODERATE] style_issue
      Function 'calculate' is missing a docstring
   2. [HIGH] style_issue
      Avoid bare except clauses - specify exception types

🔄 SELF-HEALING: SUCCESS
   ✓ Code generation instructions have been updated!
   ✓ Changes: Instructions improved for better code quality
   ✓ System will now generate better code in future attempts
```

## Configuration

### Custom Validation Rules

You can customize the style rules in `PythonCodeValidator`:

```python
STYLE_RULES = {
    "no_tabs": {
        "enabled": True,
        "severity": "moderate",
        "message": "Use spaces instead of tabs"
    },
    "require_docstrings": {
        "enabled": True,
        "severity": "moderate",
        "message": "Functions should have docstrings"
    },
    "max_line_length": {
        "enabled": True,
        "severity": "low",
        "limit": 120,
        "message": "Lines should not exceed 120 characters"
    },
    "no_bare_except": {
        "enabled": True,
        "severity": "high",
        "message": "Avoid bare except - specify exception types"
    },
}
```

### Disable Style Checking

If you only want syntax validation:

```python
code_validator = PythonCodeValidator(check_style=False)
system.add_validator(code_validator)
```

### Adjust AI Model Settings

```python
config = SystemConfig(
    main_model="gpt-4o-mini",
    main_model_provider="openai",
    enable_auto_optimization=True,
    temperature_main=0.3,  # Lower = more consistent code
    temperature_critic=0.1,  # Lower = more precise analysis
)
```

## Use Cases

### 1. AI-Powered Code Completion
- Generate function implementations from docstrings
- Create boilerplate code from descriptions
- Auto-complete partial code snippets

### 2. Code Generation from Requirements
- Convert natural language specs to working code
- Generate test cases from function signatures
- Create API endpoints from specifications

### 3. Educational Tools
- Help students learn Python by example
- Generate code with explanations
- Demonstrate best practices automatically

### 4. Rapid Prototyping
- Quickly scaffold new projects
- Generate utility functions on demand
- Create test fixtures and mock data

### 5. Code Refactoring Assistant
- Improve existing code quality
- Enforce style guidelines automatically
- Modernize legacy code patterns

## Advanced Features

### Code Extraction
The validator automatically extracts code from:
- Markdown code blocks: ` ```python ... ``` `
- Plain text Python code
- Mixed format outputs

### Error Context
Syntax errors include:
- Line numbers where errors occur
- The problematic line of code
- Description of what went wrong

### Progressive Learning
The system maintains a version history showing:
- What triggers caused updates
- What changes were made
- How instructions evolved over time

## Integration

### Add to Your Workflow

```python
from examples.self_healing_code_assistant import PythonCodeValidator

# In your application
system = SelfOptimizingSystem(config)
system.add_validator(PythonCodeValidator(check_style=True))

# Generate code
result = system.execute("Create a function to calculate factorial")

if result['validation_passed']:
    # Code is ready to use
    generated_code = result['output']
else:
    # System is learning and will improve
    print("Code quality issues detected, system is self-optimizing...")
```

### CI/CD Integration

You can use this pattern in continuous integration:

```python
def validate_ai_generated_code(code_prompt):
    system = SelfOptimizingSystem(config)
    system.add_validator(PythonCodeValidator())
    
    result = system.execute(code_prompt)
    
    # Fail the build if code doesn't validate
    assert result['validation_passed'], "Generated code failed validation"
    
    return result['output']
```

## Limitations

### Current Scope
- **Python Only**: Currently validates Python syntax only
- **Style Rules**: Limited to common style issues (extensible)
- **Static Analysis**: Doesn't execute code or check runtime behavior
- **Single File**: Designed for single-file code generation

### Future Enhancements
- Support for multiple programming languages
- Integration with pylint, flake8, or black for advanced linting
- Security vulnerability scanning (e.g., SQL injection, XSS)
- Unit test generation and validation
- Code complexity metrics (cyclomatic complexity)
- Import statement validation

## Testing

The example includes several test cases:

1. **Baseline Test**: Simple hello world function
2. **Simple Calculator**: Basic arithmetic function
3. **List Processing**: Filtering even numbers
4. **String Manipulation**: Reversing words

Each test demonstrates:
- Code generation request
- Validation process
- Success/failure handling
- Self-optimization triggers

## Comparison to Other Examples

| Feature | Self-Healing Code | Hallucination-Proof | Adversarial Hardener |
|---------|------------------|---------------------|---------------------|
| **Focus** | Code quality | Data accuracy | Security |
| **Validation** | Syntax + Style | Grounding check | Leak detection |
| **Use Case** | Code generation | Data extraction | Prompt protection |
| **Failure Type** | Syntax/style errors | Hallucinations | Jailbreak attempts |

## Key Takeaways

1. **Validation Before Execution**: Catch errors in generated code before they cause problems
2. **Automated Quality**: Enforce coding standards without manual review
3. **Continuous Improvement**: System learns from failures to generate better code
4. **Production Ready**: Pattern suitable for real-world code generation workflows
5. **Extensible**: Easy to add new validation rules or support new languages

## Next Steps

1. **Try It**: Run the example with different code generation tasks
2. **Customize**: Modify validation rules to match your style guide
3. **Extend**: Add support for other languages or validation types
4. **Integrate**: Incorporate into your development workflow
5. **Experiment**: Test with different AI models and configurations

## Resources

- [Main README](../README.md) - Project overview
- [Examples README](README.md) - All examples
- [API Reference](../docs/api-reference.md) - API documentation
- [Python AST Documentation](https://docs.python.org/3/library/ast.html) - AST module reference

## Contributing

Have ideas for improving the code validator? We welcome contributions!

1. Add new validation rules
2. Support additional programming languages
3. Integrate advanced linting tools
4. Add security checks
5. Improve error messages

## License

Part of the autonomai project, licensed under the MIT License.
