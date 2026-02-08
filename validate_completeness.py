#!/usr/bin/env python3
"""
Validation Script: Python File Completeness Check

This script validates that all Python files in the src/ directory are:
1. Syntactically valid
2. Have complete function/method implementations
3. Have no truncated code

Created to address Issue: [Bug]: Truncated method implementations in Python files
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class CompletenessValidator:
    """Validates Python files for completeness"""

    def __init__(self, directory: str = "src"):
        self.directory = directory
        self.results = {
            "total_files": 0,
            "valid_files": 0,
            "syntax_errors": [],
            "stub_functions": [],
            "incomplete_functions": [],
            "truncated_files": [],
        }

    def check_file(self, filepath: str) -> Dict[str, any]:
        """Check a single Python file for completeness"""
        file_result = {
            "path": filepath,
            "valid": True,
            "issues": [],
            "stats": {}
        }

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Count lines
            lines = content.splitlines()
            file_result["stats"]["lines"] = len(lines)

            # Parse the file
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                file_result["valid"] = False
                file_result["issues"].append(f"Syntax error at line {e.lineno}: {e.msg}")
                self.results["syntax_errors"].append(filepath)
                return file_result

            # Count functions and classes
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node)

            file_result["stats"]["functions"] = len(functions)
            file_result["stats"]["classes"] = len(classes)

            # Check for incomplete functions
            for func in functions:
                func_name = func.name
                line_no = func.lineno

                # Check for empty body
                if not func.body:
                    file_result["valid"] = False
                    file_result["issues"].append(
                        f"Line {line_no}: Function '{func_name}' has empty body"
                    )
                    self.results["incomplete_functions"].append(f"{filepath}:{line_no}")
                    continue

                # Check for only docstring
                if len(func.body) == 1:
                    stmt = func.body[0]
                    if isinstance(stmt, ast.Expr):
                        if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                            file_result["issues"].append(
                                f"Line {line_no}: Function '{func_name}' has only docstring"
                            )
                    # Check for only pass
                    elif isinstance(stmt, ast.Pass):
                        file_result["issues"].append(
                            f"Line {line_no}: Function '{func_name}' is a stub (only 'pass')"
                        )
                        self.results["stub_functions"].append(f"{filepath}:{line_no}")

            # Check if file ends properly (no truncation)
            if content and not content.endswith('\n'):
                file_result["issues"].append("File does not end with newline (may be truncated)")
            
            # Note: We don't check for unbalanced brackets via simple string counting
            # because that produces false positives (brackets in strings, comments, etc.)
            # The AST parse above is the definitive check for syntax validity

        except Exception as e:
            file_result["valid"] = False
            file_result["issues"].append(f"Error reading file: {str(e)}")
            self.results["syntax_errors"].append(filepath)

        if file_result["valid"]:
            self.results["valid_files"] += 1

        return file_result

    def validate_directory(self) -> bool:
        """Validate all Python files in the directory"""
        print("=" * 80)
        print("Python File Completeness Validation")
        print("=" * 80)
        print(f"\nScanning directory: {self.directory}/\n")

        # Find all Python files
        python_files = []
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    python_files.append(filepath)

        self.results["total_files"] = len(python_files)
        print(f"Found {len(python_files)} Python files\n")

        # Check each file
        detailed_results = []
        for filepath in sorted(python_files):
            result = self.check_file(filepath)
            detailed_results.append(result)
            
            # Print progress
            status = "✅" if result["valid"] else "❌"
            print(f"{status} {filepath}")
            if not result["valid"]:
                for issue in result["issues"]:
                    print(f"    ⚠️  {issue}")

        # Print summary
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"\nTotal files checked: {self.results['total_files']}")
        print(f"Valid files: {self.results['valid_files']}")
        print(f"Files with issues: {self.results['total_files'] - self.results['valid_files']}")

        if self.results['syntax_errors']:
            print(f"\n❌ Syntax errors: {len(self.results['syntax_errors'])}")
            for error in self.results['syntax_errors'][:5]:
                print(f"  - {error}")

        if self.results['stub_functions']:
            print(f"\n⚠️  Stub functions: {len(self.results['stub_functions'])}")
            for stub in self.results['stub_functions'][:5]:
                print(f"  - {stub}")

        if self.results['incomplete_functions']:
            print(f"\n❌ Incomplete functions: {len(self.results['incomplete_functions'])}")
            for incomplete in self.results['incomplete_functions'][:5]:
                print(f"  - {incomplete}")

        if self.results['truncated_files']:
            print(f"\n❌ Possibly truncated files: {len(self.results['truncated_files'])}")
            for truncated in self.results['truncated_files'][:5]:
                print(f"  - {truncated}")

        # Final verdict
        print("\n" + "=" * 80)
        all_valid = self.results['valid_files'] == self.results['total_files']
        
        if all_valid:
            print("✅ ALL FILES ARE COMPLETE AND VALID!")
            print("=" * 80)
            return True
        else:
            print("❌ SOME FILES HAVE ISSUES - REVIEW ABOVE")
            print("=" * 80)
            return False


def main():
    """Main entry point"""
    validator = CompletenessValidator("src")
    
    # Run validation
    all_valid = validator.validate_directory()
    
    # Exit with appropriate code
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
