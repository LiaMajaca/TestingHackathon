#!/usr/bin/env python3
"""
Comprehensive codebase analyzer for testing and documentation gaps.
Analyzes functions, classes, and methods across multiple languages.
Usage: python3 testbot.py
"""

import os
import re
import glob
import sys
import argparse
from collections import defaultdict

def find_code_elements(file_path, api_only=False):
    """Extract functions, classes, and methods from a file."""
    elements = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if api_only:
            # API endpoint scanning mode
            elements = find_api_endpoints(content, file_ext)
        else:
            # Full codebase analysis mode
            if file_ext == '.py':
                elements = find_python_elements(content)
            elif file_ext in ['.js', '.ts']:
                elements = find_javascript_elements(content)
            elif file_ext == '.java':
                elements = find_java_elements(content)
            
    except Exception:
        pass
        
    return elements

def find_api_endpoints(content, file_ext):
    """Find API endpoints in web frameworks."""
    elements = []
    
    if file_ext == '.py':
        # Python patterns: @app.route('/api/...') or @app.get('/api/...')
        python_patterns = [
            r'@app\.route\([\'"]([^\'"]+)[\'"]',
            r'@app\.get\([\'"]([^\'"]+)[\'"]',
            r'@router\.get\([\'"]([^\'"]+)[\'"]',
            r'@router\.post\([\'"]([^\'"]+)[\'"]',
            r'@router\.put\([\'"]([^\'"]+)[\'"]',
            r'@router\.delete\([\'"]([^\'"]+)[\'"]'
        ]
        
        for pattern in python_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match.startswith('/api/') and not match.endswith('...'):
                    elements.append((match, 'endpoint', content))
                    
    elif file_ext in ['.js', '.ts']:
        # Node.js patterns: app.get('/api/...') or router.get('/api/...')
        nodejs_patterns = [
            r'\.get\([\'"]([^\'"]+)[\'"]',
            r'\.post\([\'"]([^\'"]+)[\'"]',
            r'\.put\([\'"]([^\'"]+)[\'"]',
            r'\.delete\([\'"]([^\'"]+)[\'"]'
        ]
        
        for pattern in nodejs_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match.startswith('/api/') and not match.endswith('...'):
                    elements.append((match, 'endpoint', content))
    
    return elements

def find_python_elements(content):
    """Find Python functions and classes."""
    elements = []
    
    # Functions: def function_name(, async def function_name(
    function_patterns = [
        r'def\s+(\w+)\s*\(',
        r'async\s+def\s+(\w+)\s*\('
    ]
    
    # Classes: class ClassName(, class ClassName:
    class_patterns = [
        r'class\s+(\w+)\s*[\(:]'
    ]
    
    for pattern in function_patterns + class_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            name = match.group(1)
            if not name.startswith('_'):  # Skip private methods
                elements.append((name, 'function' if 'def' in pattern else 'class', content))
    
    return elements

def find_javascript_elements(content):
    """Find JavaScript/TypeScript functions, classes, and exports."""
    elements = []
    
    # Function patterns
    patterns = [
        r'function\s+(\w+)\s*\(',
        r'const\s+(\w+)\s*=\s*(?:async\s+)?\(',  # Arrow functions
        r'let\s+(\w+)\s*=\s*(?:async\s+)?\(',
        r'var\s+(\w+)\s*=\s*(?:async\s+)?\(',
        r'class\s+(\w+)\s*[\(\{]',
        r'export\s+(?:function|const|class)\s+(\w+)',
        r'export\s*\{\s*(\w+)',
        r'(\w+)\s*:\s*(?:async\s+)?function',  # Object methods
        r'(\w+)\s*:\s*(?:async\s+)?\('  # Object arrow methods
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            name = match.group(1)
            if not name.startswith('_'):  # Skip private methods
                element_type = 'class' if 'class' in pattern else 'function'
                elements.append((name, element_type, content))
    
    return elements

def find_java_elements(content):
    """Find Java methods and classes."""
    elements = []
    
    # Method patterns: public/private/protected returnType methodName(
    method_patterns = [
        r'(?:public|private|protected)\s+\w+(?:<[^>]*>)?\s+(\w+)\s*\(',
        r'(?:public|private|protected)\s+(\w+)\s*\('  # Constructor
    ]
    
    # Class patterns
    class_patterns = [
        r'(?:public|private|protected)?\s*class\s+(\w+)\s*[\(\{]'
    ]
    
    for pattern in method_patterns + class_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            name = match.group(1)
            if not name.startswith('_'):  # Skip private methods
                element_type = 'class' if 'class' in pattern else 'method'
                elements.append((name, element_type, content))
    
    return elements

def analyze_documentation(element_name, content, file_path):
    """Analyze documentation quality for a code element."""
    doc_score = 0
    max_score = 4
    
    # Find the element in the content
    element_pattern = re.escape(element_name)
    
    # Look for docstring/comment before the element
    patterns = [
        rf'""".*?""".*?{element_pattern}',  # Python docstring before
        rf"'''.*?'''.*?{element_pattern}",  # Python docstring before
        rf'/\*\*.*?\*/.*?{element_pattern}',  # JSDoc before
        rf'//.*?{element_pattern}',  # Single line comment before
    ]
    
    has_docstring = False
    for pattern in patterns:
        if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
            has_docstring = True
            break
    
    # Check for parameter documentation
    has_params = bool(re.search(r'@param|Parameters?:|Args?:', content, re.IGNORECASE))
    
    # Check for return value documentation
    has_return = bool(re.search(r'@return|@returns|Returns?:|Return type:', content, re.IGNORECASE))
    
    # Check for examples or clear descriptions
    has_examples = bool(re.search(r'@example|Example:|Examples?:|Usage:', content, re.IGNORECASE))
    
    if has_docstring:
        doc_score += 1
    if has_params:
        doc_score += 1
    if has_return:
        doc_score += 1
    if has_examples:
        doc_score += 1
    
    return doc_score, max_score

def generate_docstring(function_name, content, file_path):
    """Generate a basic docstring for a function."""
    # Extract function signature to get parameters
    function_pattern = rf'def\s+{re.escape(function_name)}\s*\(([^)]*)\)'
    match = re.search(function_pattern, content)
    
    if not match:
        return None
    
    params_str = match.group(1).strip()
    params = []
    
    if params_str:
        # Parse parameters
        for param in params_str.split(','):
            param = param.strip()
            if '=' in param:
                param = param.split('=')[0].strip()
            if param and not param.startswith('*'):
                params.append(param)
    
    # Generate function description based on name patterns
    description = generate_function_description(function_name)
    
    # Generate parameter documentation
    param_docs = []
    for param in params:
        param_desc = generate_parameter_description(param)
        param_docs.append(f"        {param}: {param_desc}")
    
    # Generate return type documentation
    return_type = generate_return_type(function_name)
    
    # Build docstring
    docstring = f'    """\n    {description}\n'
    
    if param_docs:
        docstring += '    \n    Args:\n'
        docstring += '\n'.join(param_docs)
    
    if return_type:
        docstring += f'\n    \n    Returns:\n        {return_type}'
    
    docstring += '\n    """'
    
    return docstring

def generate_function_description(function_name):
    """Generate function description based on name patterns."""
    name_lower = function_name.lower()
    
    if name_lower.startswith('get_'):
        object_name = name_lower[4:].replace('_', ' ')
        return f"Retrieves {object_name} information"
    elif name_lower.startswith('create_'):
        object_name = name_lower[7:].replace('_', ' ')
        return f"Creates new {object_name}"
    elif name_lower.startswith('calculate_'):
        value_name = name_lower[10:].replace('_', ' ')
        return f"Calculates {value_name}"
    elif name_lower.startswith('process_'):
        operation_name = name_lower[8:].replace('_', ' ')
        return f"Processes {operation_name}"
    elif name_lower.startswith('validate_'):
        input_name = name_lower[9:].replace('_', ' ')
        return f"Validates {input_name}"
    elif name_lower.startswith('update_'):
        object_name = name_lower[7:].replace('_', ' ')
        return f"Updates {object_name}"
    elif name_lower.startswith('delete_'):
        object_name = name_lower[7:].replace('_', ' ')
        return f"Deletes {object_name}"
    elif name_lower.startswith('check_'):
        condition_name = name_lower[6:].replace('_', ' ')
        return f"Checks {condition_name}"
    else:
        return f"Performs {function_name.replace('_', ' ')} operation"

def generate_parameter_description(param_name):
    """Generate parameter description based on name patterns."""
    name_lower = param_name.lower()
    
    if 'id' in name_lower:
        if 'user' in name_lower:
            return "User identifier"
        elif 'order' in name_lower:
            return "Order identifier"
        else:
            return "Identifier"
    elif 'email' in name_lower:
        return "Email address"
    elif 'amount' in name_lower or 'price' in name_lower or 'cost' in name_lower:
        return "Amount in USD"
    elif 'data' in name_lower:
        return "Input data"
    elif 'name' in name_lower:
        return "Name value"
    elif 'date' in name_lower or 'time' in name_lower:
        return "Date/time value"
    elif 'status' in name_lower:
        return "Status value"
    elif 'type' in name_lower:
        return "Type specification"
    elif 'count' in name_lower or 'num' in name_lower:
        return "Numeric count"
    elif 'flag' in name_lower or 'enable' in name_lower:
        return "Boolean flag"
    else:
        return f"{param_name.replace('_', ' ')} parameter"

def generate_return_type(function_name):
    """Generate return type based on function name patterns."""
    name_lower = function_name.lower()
    
    if name_lower.startswith('get_') or name_lower.startswith('find_'):
        return "Object: Retrieved data"
    elif name_lower.startswith('create_') or name_lower.startswith('add_'):
        return "Object: Created item"
    elif name_lower.startswith('calculate_') or name_lower.startswith('compute_'):
        return "float: Calculated value"
    elif name_lower.startswith('validate_') or name_lower.startswith('check_'):
        return "bool: Validation result"
    elif name_lower.startswith('process_') or name_lower.startswith('handle_'):
        return "Object: Processed result"
    elif name_lower.startswith('update_') or name_lower.startswith('modify_'):
        return "Object: Updated item"
    elif name_lower.startswith('delete_') or name_lower.startswith('remove_'):
        return "bool: Success status"
    else:
        return "Object: Operation result"

def find_function_for_endpoint(endpoint, content):
    """Find the function name associated with an API endpoint."""
    # Look for the function definition after the endpoint decorator
    endpoint_pattern = re.escape(endpoint)
    pattern = rf'@.*?{endpoint_pattern}.*?\n.*?def\s+(\w+)\s*\('
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        return match.group(1)
    
    return None

def add_docstring_to_file(file_path, function_name, docstring):
    """Add docstring to a function in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find the function definition
        function_pattern = rf'(def\s+{re.escape(function_name)}\s*\([^)]*\))'
        match = re.search(function_pattern, content)
        
        if not match:
            return False
        
        function_def = match.group(1)
        
        # Check if function already has a docstring
        after_def = content[match.end():]
        next_line_match = re.search(r'\n\s*"""', after_def)
        
        if next_line_match:
            # Function already has a docstring, skip
            return False
        
        # Find the end of the function definition line
        def_end = match.end()
        
        # Find the next line after the function definition
        next_line_start = content.find('\n', def_end)
        if next_line_start == -1:
            next_line_start = len(content)
        else:
            next_line_start += 1
        
        # Insert docstring after the function definition
        new_content = content[:next_line_start] + docstring + '\n' + content[next_line_start:]
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
        
    except Exception:
        return False

def check_test_exists(element_name, file_path):
    """Check if test file exists for the element."""
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Look for test files in the same directory and subdirectories
    search_dirs = [os.path.dirname(file_path), '.']
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
            
        if file_ext == '.py':
            test_patterns = [
                f"test_{base_name}.py",
                f"test_{element_name}.py",
                f"{base_name}_test.py",
                f"{element_name}_test.py"
            ]
        elif file_ext in ['.js', '.ts']:
            test_patterns = [
                f"{base_name}.test.js",
                f"{base_name}.spec.js",
                f"{element_name}.test.js",
                f"{element_name}.spec.js"
            ]
        elif file_ext == '.java':
            test_patterns = [
                f"{base_name}Test.java",
                f"{base_name}Tests.java",
                f"{element_name}Test.java",
                f"{element_name}Tests.java"
            ]
        else:
            continue
        
        for test_pattern in test_patterns:
            test_files = glob.glob(os.path.join(search_dir, "**", test_pattern), recursive=True)
            if test_files:
                return test_files[0]
                
    return None

def assess_risk(has_tests, doc_score, max_doc_score):
    """Assess risk level based on tests and documentation."""
    if not has_tests and doc_score < 2:
        return "HIGH RISK"
    elif not has_tests and doc_score >= 2:
        return "MEDIUM RISK"
    elif has_tests and doc_score < 2:
        return "MEDIUM RISK"
    else:  # has_tests and good docs
        return "LOW RISK"

def scan_codebase(fix_docs=False, api_only=False):
    """Scan the codebase for functions, classes, and methods."""
    if api_only:
        if fix_docs:
            print("🔍 Scanning for API endpoints and fixing documentation...\n")
        else:
            print("🔍 Scanning for API endpoints...\n")
    else:
        if fix_docs:
            print("🔍 Scanning codebase and fixing documentation...\n")
        else:
            print("🔍 Scanning codebase for functions, classes, and methods...\n")
    
    # Find all source files
    file_patterns = ['**/*.py', '**/*.js', '**/*.ts', '**/*.java']
    all_files = []
    
    for pattern in file_patterns:
        all_files.extend(glob.glob(pattern, recursive=True))
    
    # Filter out common non-source directories
    exclude_dirs = {'node_modules', '.git', '__pycache__', '.venv', 'venv', 'env', 'target', 'build'}
    filtered_files = []
    
    for file_path in all_files:
        if not any(exclude_dir in file_path for exclude_dir in exclude_dirs):
            filtered_files.append(file_path)
    
    # Group elements by file
    file_elements = defaultdict(list)
    
    for file_path in filtered_files:
        elements = find_code_elements(file_path, api_only)
        for element_name, element_type, content in elements:
            file_elements[file_path].append((element_name, element_type, content))
    
    # Analyze and output results
    total_elements = 0
    need_tests = 0
    need_docs = 0
    high_risk = []
    documented_count = 0
    
    for file_path, elements in sorted(file_elements.items()):
        if not elements:
            continue
            
        print(f"📁 FILE: {os.path.basename(file_path)}")
        
        for element_name, element_type, content in elements:
            total_elements += 1
            
            test_file = check_test_exists(element_name, file_path)
            has_tests = test_file is not None
            
            doc_score, max_doc_score = analyze_documentation(element_name, content, file_path)
            risk_level = assess_risk(has_tests, doc_score, max_doc_score)
            
            if not has_tests:
                need_tests += 1
            if doc_score < 2:
                need_docs += 1
            if risk_level == "HIGH RISK":
                high_risk.append(element_name)
            
            # Fix documentation if requested and needed
            if fix_docs and doc_score < 2 and file_path.endswith('.py'):
                if element_type == 'function':
                    docstring = generate_docstring(element_name, content, file_path)
                    if docstring and add_docstring_to_file(file_path, element_name, docstring):
                        documented_count += 1
                        print(f"  📝 Added documentation to {element_name}()")
                        # Re-analyze after adding documentation
                        doc_score = 3  # Assume good docs after adding
                        risk_level = assess_risk(has_tests, doc_score, max_doc_score)
                elif element_type == 'endpoint':
                    # For API endpoints, find the associated function and document it
                    function_name = find_function_for_endpoint(element_name, content)
                    if function_name:
                        docstring = generate_docstring(function_name, content, file_path)
                        if docstring and add_docstring_to_file(file_path, function_name, docstring):
                            documented_count += 1
                            print(f"  📝 Added documentation to {function_name}() for endpoint {element_name}")
                            # Re-analyze after adding documentation
                            doc_score = 3  # Assume good docs after adding
                            risk_level = assess_risk(has_tests, doc_score, max_doc_score)
            
            # Determine status icons and messages
            if has_tests and doc_score >= 3:
                status_icon = "✅"
                status_msg = f"HAS TESTS + GOOD DOCS"
            elif has_tests and doc_score < 2:
                status_icon = "⚠️"
                status_msg = f"HAS TESTS but POOR DOCS"
            elif not has_tests and doc_score >= 2:
                status_icon = "❌"
                status_msg = f"NO TESTS + GOOD DOCS"
            else:  # no tests and poor docs
                status_icon = "❌"
                status_msg = f"NO TESTS + NO DOCS"
            
            print(f"  {status_icon} {element_name}() - {status_msg} ({risk_level})")
        
        print()  # Empty line between files
    
    # Summary
    if total_elements > 0:
        print("📊 SUMMARY:")
        print(f"- Total functions analyzed: {total_elements}")
        print(f"- Need tests: {need_tests} ({need_tests/total_elements*100:.0f}%)")
        print(f"- Need docs: {need_docs} ({need_docs/total_elements*100:.0f}%)")
        print(f"- High risk (no tests + no docs): {len(high_risk)}")
        
        if fix_docs and documented_count > 0:
            print(f"📝 Functions documented: {documented_count}")
        
        if high_risk:
            print(f"🎯 PRIORITY: Focus on {', '.join(high_risk[:3])}{'...' if len(high_risk) > 3 else ''}")
    else:
        print("No functions, classes, or methods found in the codebase.")

def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(description='Analyze codebase for testing and documentation gaps')
    parser.add_argument('--fix-docs', action='store_true', 
                       help='Automatically generate documentation for functions with no docs')
    parser.add_argument('--api-only', action='store_true',
                       help='Scan only for API endpoints (Flask/FastAPI/Express routes)')
    
    args = parser.parse_args()
    
    scan_codebase(fix_docs=args.fix_docs, api_only=args.api_only)

if __name__ == "__main__":
    main()