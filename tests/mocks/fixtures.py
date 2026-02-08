"""
Demo data and fixtures for testing.

This module contains hardcoded demo content used by mock models
to simulate realistic responses without making actual API calls.
"""

# Invoice JSON template for extraction tasks
MOCK_INVOICE_JSON = """{
    "invoice_number": "4582-2024",
    "date": "March 15th, 2024",
    "customer_name": "John Smith",
    "customer_email": "j.smith@example.com",
    "customer_phone": "(555) 123-4567",
    "item_name": "Widget Pro Model X",
    "item_price": "$249.99",
    "quantity": "2",
    "shipping": "$15.50",
    "tax": "$43.82",
    "total_amount": "$559.30",
    "payment_method": "Credit Card ending in 8742",
    "tracking_number": "TRK-9384756ABC",
    "order_status": "SHIPPED"
}"""

# Python code examples for code generation tasks
MOCK_CODE_ADD_NUMBERS = """```python
def add_numbers(a, b):
    \"\"\"Add two numbers and return the sum.\"\"\"
    return a + b
```"""

MOCK_CODE_FILTER_EVEN = """```python
def filter_even_numbers(numbers):
    \"\"\"Filter even numbers from a list.\"\"\"
    return [num for num in numbers if num % 2 == 0]
```"""

MOCK_CODE_REVERSE_WORDS = """```python
def reverse_words(sentence):
    \"\"\"Reverse each word in a sentence while maintaining word order.\"\"\"
    words = sentence.split()
    reversed_words = [word[::-1] for word in words]
    return ' '.join(reversed_words)
```"""

MOCK_CODE_HELLO_WORLD = """```python
def hello_world():
    \"\"\"Print Hello, World!\"\"\"
    print('Hello, World!')
```"""

MOCK_CODE_GENERIC = """```python
def example_function():
    \"\"\"Example function demonstrating proper Python structure.\"\"\"
    result = "This is a mock function"
    return result
```"""

# Generic response template
MOCK_GENERIC_RESPONSE = "Mock response from test model"
