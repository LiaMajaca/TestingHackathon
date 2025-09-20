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
            elif file_ext == '.cs':
                elements = find_csharp_elements(content)
            
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

def find_csharp_elements(content):
    """Find C# methods and classes."""
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
    """Generate language-specific documentation for a function."""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Detect indentation style
    indent_size, indent_type = detect_indentation_style(content)
    
    # Extract function signature to get parameters
    if file_ext == '.py':
        function_pattern = rf'def\s+{re.escape(function_name)}\s*\(([^)]*)\)'
    elif file_ext in ['.js', '.ts']:
        function_pattern = rf'(?:function\s+{re.escape(function_name)}|{re.escape(function_name)}\s*=\s*(?:async\s+)?\()\s*\(([^)]*)\)'
    elif file_ext == '.java':
        function_pattern = rf'(?:public|private|protected)\s+\w+(?:<[^>]*>)?\s+{re.escape(function_name)}\s*\(([^)]*)\)'
    elif file_ext == '.cs':
        function_pattern = rf'(?:public|private|protected)\s+\w+(?:<[^>]*>)?\s+{re.escape(function_name)}\s*\(([^)]*)\)'
    else:
        return None
    
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
            if param and not param.startswith('*') and param != 'self':
                params.append(param)
    
    # Generate language-specific documentation
    if file_ext == '.py':
        return generate_python_docstring(function_name, params, indent_size, indent_type)
    elif file_ext in ['.js', '.ts']:
        return generate_javascript_jsdoc(function_name, params, indent_size, indent_type)
    elif file_ext == '.java':
        return generate_java_javadoc(function_name, params, indent_size, indent_type)
    elif file_ext == '.cs':
        return generate_csharp_xmldoc(function_name, params, indent_size, indent_type)
    
    return None

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

def analyze_security_risks(element_name, content, file_path, has_tests, doc_score):
    """Analyze security risks for a function or method."""
    security_issues = []
    risk_level = "LOW"
    
    # 1. FINANCIAL FUNCTIONS WITHOUT TESTS
    financial_keywords = ['payment', 'charge', 'billing', 'money', 'price', 'cost', 'transaction', 'refund', 'invoice']
    if any(keyword in element_name.lower() for keyword in financial_keywords):
        if not has_tests:
            security_issues.append("HANDLES MONEY + NO TESTS")
            risk_level = "CRITICAL"
        else:
            security_issues.append("HANDLES MONEY")
            risk_level = "HIGH" if risk_level == "LOW" else risk_level
    
    # 2. AUTHENTICATION RISKS
    auth_keywords = ['auth', 'login', 'password', 'token', 'session', 'credential', 'signin', 'signup']
    if any(keyword in element_name.lower() for keyword in auth_keywords):
        if not has_tests:
            security_issues.append("AUTH FUNCTION + NO TESTS")
            risk_level = "CRITICAL"
        else:
            security_issues.append("AUTH FUNCTION")
            risk_level = "HIGH" if risk_level == "LOW" else risk_level
    
    # 3. INPUT VALIDATION GAPS
    input_keywords = ['input', 'upload', 'file', 'form', 'submit', 'validate', 'sanitize']
    if any(keyword in element_name.lower() for keyword in input_keywords):
        if not has_tests:
            security_issues.append("INPUT HANDLING + NO TESTS")
            risk_level = "HIGH" if risk_level == "LOW" else risk_level
    
    # 4. CRYPTOGRAPHIC WEAKNESSES
    crypto_keywords = ['encrypt', 'decrypt', 'hash', 'sign', 'verify', 'crypto', 'random', 'key']
    if any(keyword in element_name.lower() for keyword in crypto_keywords):
        if not has_tests:
            security_issues.append("CRYPTO FUNCTION + NO TESTS")
            risk_level = "HIGH" if risk_level == "LOW" else risk_level
    
    # Check for hardcoded secrets in function content
    if check_hardcoded_secrets(content):
        security_issues.append("HARDCODED SECRETS")
        risk_level = "CRITICAL"
    
    # Check for weak random generation
    if check_weak_random(content):
        security_issues.append("WEAK RANDOM GENERATION")
        risk_level = "CRITICAL"
    
    # Check for SQL injection risks
    if check_sql_injection_risk(content):
        security_issues.append("SQL INJECTION RISK")
        risk_level = "HIGH" if risk_level == "LOW" else risk_level
    
    return security_issues, risk_level

def check_hardcoded_secrets(content):
    """Check for hardcoded secrets in code."""
    secret_patterns = [
        r'password\s*=\s*["\'][^"\']{3,}["\']',  # At least 3 chars
        r'secret\s*=\s*["\'][^"\']{3,}["\']',
        r'api_key\s*=\s*["\'][^"\']{3,}["\']',
        r'private_key\s*=\s*["\'][^"\']{3,}["\']',
        r'token\s*=\s*["\'][^"\']{3,}["\']'
    ]
    
    # Exclude common test patterns
    exclude_patterns = [
        r'test_',
        r'example',
        r'sample',
        r'demo',
        r'placeholder'
    ]
    
    for pattern in secret_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            # Check if this is not in a test context
            is_test_context = any(re.search(exclude, content, re.IGNORECASE) for exclude in exclude_patterns)
            if not is_test_context:
                return True
    return False

def check_weak_random(content):
    """Check for weak random generation."""
    weak_random_patterns = [
        r'Math\.random\(\)',
        r'random\.random\(\)',
        r'new\s+Random\(\)',
        r'rand\(\)'
    ]
    
    # Only check for weak random in security-sensitive contexts
    security_contexts = [
        r'token',
        r'password',
        r'key',
        r'secret',
        r'encrypt',
        r'decrypt',
        r'auth',
        r'login'
    ]
    
    # Check if function is in a security context
    has_security_context = any(re.search(context, content, re.IGNORECASE) for context in security_contexts)
    
    if not has_security_context:
        return False
    
    for pattern in weak_random_patterns:
        if re.search(pattern, content):
            return True
    return False

def check_sql_injection_risk(content):
    """Check for potential SQL injection risks."""
    sql_patterns = [
        r'SELECT.*\+.*\$',
        r'INSERT.*\+.*\$',
        r'UPDATE.*\+.*\$',
        r'DELETE.*\+.*\$',
        r'query\s*=\s*["\'][^"\']*\+[^"\']*["\']',
        r'execute\s*\(\s*["\'][^"\']*\+[^"\']*["\']'
    ]
    
    # Only check for SQL injection in database-related contexts
    db_contexts = [
        r'database',
        r'db\.',
        r'query',
        r'execute',
        r'select',
        r'insert',
        r'update',
        r'delete'
    ]
    
    has_db_context = any(re.search(context, content, re.IGNORECASE) for context in db_contexts)
    
    if not has_db_context:
        return False
    
    for pattern in sql_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False

def detect_indentation_style(content):
    """Detect the indentation style used in a file."""
    lines = content.split('\n')
    indentations = []
    
    for line in lines:
        if line.strip():  # Non-empty line
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces > 0:
                indentations.append(leading_spaces)
    
    if not indentations:
        return 4, 'spaces'  # Default to 4 spaces
    
    # Find the most common indentation
    indent_counts = {}
    for indent in indentations:
        indent_counts[indent] = indent_counts.get(indent, 0) + 1
    
    most_common_indent = max(indent_counts, key=indent_counts.get)
    
    # Determine if it's spaces or tabs
    sample_line = next((line for line in lines if line.strip() and len(line) - len(line.lstrip()) == most_common_indent), None)
    if sample_line and sample_line.startswith('\t'):
        return 1, 'tabs'
    else:
        return most_common_indent, 'spaces'

def generate_python_docstring(function_name, params, indent_size, indent_type):
    """Generate Python docstring with proper indentation."""
    description = generate_function_description(function_name)
    return_type = generate_return_type(function_name)
    
    # Generate parameter documentation
    param_docs = []
    for param in params:
        param_desc = generate_parameter_description(param)
        param_docs.append(f"{param}: {param_desc}")
    
    # Build docstring with proper indentation
    indent = '\t' if indent_type == 'tabs' else ' ' * indent_size
    docstring_lines = ['"""', description]
    
    if param_docs:
        docstring_lines.append('')
        docstring_lines.append('Args:')
        for param_doc in param_docs:
            docstring_lines.append(f'    {param_doc}')
    
    if return_type:
        docstring_lines.append('')
        docstring_lines.append('Returns:')
        docstring_lines.append(f'    {return_type}')
    
    docstring_lines.append('"""')
    
    # Apply indentation to each line
    indented_lines = []
    for line in docstring_lines:
        if line.strip():
            indented_lines.append(indent + line)
        else:
            indented_lines.append('')
    
    return '\n'.join(indented_lines)

def generate_javascript_jsdoc(function_name, params, indent_size, indent_type):
    """Generate JavaScript JSDoc comment with proper indentation."""
    description = generate_function_description(function_name)
    return_type = generate_return_type(function_name)
    
    # Generate parameter documentation
    param_docs = []
    for param in params:
        param_desc = generate_parameter_description(param)
        param_type = 'Object' if 'data' in param.lower() else 'string' if 'name' in param.lower() else 'number'
        param_docs.append(f" * @param {{{param_type}}} {param} {param_desc}")
    
    # Build JSDoc comment
    indent = '\t' if indent_type == 'tabs' else ' ' * indent_size
    jsdoc_lines = ['/**', f' * {description}']
    
    if param_docs:
        jsdoc_lines.append(' *')
        jsdoc_lines.extend(param_docs)
    
    if return_type:
        jsdoc_lines.append(' *')
        return_type_js = 'Object' if 'Object' in return_type else 'boolean' if 'bool' in return_type else 'number'
        return_desc = return_type.split(":")[1] if ":" in return_type else return_type
        jsdoc_lines.append(f' * @returns {{{return_type_js}}} {return_desc}')
    
    jsdoc_lines.append(' */')
    
    # Apply indentation to each line
    indented_lines = []
    for line in jsdoc_lines:
        indented_lines.append(indent + line)
    
    return '\n'.join(indented_lines)

def generate_java_javadoc(function_name, params, indent_size, indent_type):
    """Generate Java Javadoc comment with proper indentation."""
    description = generate_function_description(function_name)
    return_type = generate_return_type(function_name)
    
    # Generate parameter documentation
    param_docs = []
    for param in params:
        param_desc = generate_parameter_description(param)
        param_docs.append(f" * @param {param} {param_desc}")
    
    # Build Javadoc comment
    indent = '\t' if indent_type == 'tabs' else ' ' * indent_size
    javadoc_lines = ['/**', f' * {description}']
    
    if param_docs:
        javadoc_lines.append(' *')
        javadoc_lines.extend(param_docs)
    
    if return_type:
        javadoc_lines.append(' *')
        javadoc_lines.append(f' * @return {return_type.split(":")[1] if ":" in return_type else return_type}')
    
    javadoc_lines.append(' */')
    
    # Apply indentation to each line
    indented_lines = []
    for line in javadoc_lines:
        indented_lines.append(indent + line)
    
    return '\n'.join(indented_lines)

def generate_csharp_xmldoc(function_name, params, indent_size, indent_type):
    """Generate C# XML documentation with proper indentation."""
    description = generate_function_description(function_name)
    return_type = generate_return_type(function_name)
    
    # Generate parameter documentation
    param_docs = []
    for param in params:
        param_desc = generate_parameter_description(param)
        param_docs.append(f'/// <param name="{param}">{param_desc}</param>')
    
    # Build XML documentation
    indent = '\t' if indent_type == 'tabs' else ' ' * indent_size
    xmldoc_lines = ['/// <summary>', f'/// {description}', '/// </summary>']
    
    if param_docs:
        xmldoc_lines.extend(param_docs)
    
    if return_type:
        xmldoc_lines.append(f'/// <returns>{return_type.split(":")[1] if ":" in return_type else return_type}</returns>')
    
    # Apply indentation to each line
    indented_lines = []
    for line in xmldoc_lines:
        indented_lines.append(indent + line)
    
    return '\n'.join(indented_lines)

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
    """Add language-specific documentation to a function in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Find the function definition based on language
        if file_ext == '.py':
            function_pattern = rf'(def\s+{re.escape(function_name)}\s*\([^)]*\)\s*:)'
            doc_pattern = r'\n\s*"""'
        elif file_ext in ['.js', '.ts']:
            function_pattern = rf'(function\s+{re.escape(function_name)}\s*\([^)]*\)|{re.escape(function_name)}\s*=\s*(?:async\s+)?\([^)]*\))'
            doc_pattern = r'\n\s*/\*\*'
        elif file_ext == '.java':
            function_pattern = rf'((?:public|private|protected)\s+\w+(?:<[^>]*>)?\s+{re.escape(function_name)}\s*\([^)]*\))'
            doc_pattern = r'\n\s*/\*\*'
        elif file_ext == '.cs':
            function_pattern = rf'((?:public|private|protected)\s+\w+(?:<[^>]*>)?\s+{re.escape(function_name)}\s*\([^)]*\))'
            doc_pattern = r'\n\s*///'
        else:
            return False
        
        match = re.search(function_pattern, content)
        
        if not match:
            return False
        
        # Check if function already has documentation
        after_def = content[match.end():]
        next_line_match = re.search(doc_pattern, after_def)
        
        if next_line_match:
            # Function already has documentation, skip
            return False
        
        # Find the end of the function definition line
        def_end = match.end()
        
        # Find the next line after the function definition
        next_line_start = content.find('\n', def_end)
        if next_line_start == -1:
            next_line_start = len(content)
        else:
            next_line_start += 1
        
        # Get the indentation from the function definition line
        function_line_start = content.rfind('\n', 0, match.start()) + 1
        function_line = content[function_line_start:match.end()]
        base_indent = len(function_line) - len(function_line.lstrip())
        
        # For Python, insert after function definition
        # For other languages, insert before function definition
        if file_ext == '.py':
            # Insert docstring after the function definition
            new_content = content[:next_line_start] + docstring + '\n' + content[next_line_start:]
        else:
            # Insert documentation before the function definition
            new_content = content[:match.start()] + docstring + '\n' + content[match.start():]
        
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

def scan_codebase(fix_docs=False, api_only=False, security_check=False):
    """Scan the codebase for functions, classes, and methods."""
    if security_check:
        if api_only:
            print("🔍 Scanning for API endpoints with security analysis...\n")
        else:
            print("🔍 Scanning codebase with security analysis...\n")
    elif api_only:
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
    file_patterns = ['**/*.py', '**/*.js', '**/*.ts', '**/*.java', '**/*.cs']
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
    
    # Security analysis tracking
    critical_security = []
    high_security = []
    medium_security = []
    security_recommendations = set()
    
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
            
            # Security analysis
            if security_check:
                security_issues, security_risk = analyze_security_risks(element_name, content, file_path, has_tests, doc_score)
                
                if security_risk == "CRITICAL":
                    critical_security.append((element_name, security_issues))
                elif security_risk == "HIGH":
                    high_security.append((element_name, security_issues))
                elif security_risk == "MEDIUM":
                    medium_security.append((element_name, security_issues))
                
                # Generate security recommendations
                if "HANDLES MONEY + NO TESTS" in security_issues:
                    security_recommendations.add("Add comprehensive tests for all payment functions")
                if "WEAK RANDOM GENERATION" in security_issues:
                    security_recommendations.add("Replace Math.random() with crypto-secure random")
                if "INPUT HANDLING + NO TESTS" in security_issues:
                    security_recommendations.add("Add input validation tests for user-facing functions")
                if "HARDCODED SECRETS" in security_issues:
                    security_recommendations.add("Review hardcoded values for potential secrets")
                if "SQL INJECTION RISK" in security_issues:
                    security_recommendations.add("Use parameterized queries to prevent SQL injection")
            
            if not has_tests:
                need_tests += 1
            if doc_score < 2:
                need_docs += 1
            if risk_level == "HIGH RISK":
                high_risk.append(element_name)
            
            # Fix documentation if requested and needed
            if fix_docs and doc_score < 2 and file_path.endswith(('.py', '.js', '.ts', '.java', '.cs')):
                if element_type in ['function', 'method']:
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
    
    # Security analysis output
    if security_check and (critical_security or high_security or medium_security):
        print("\n🔒 SECURITY ANALYSIS:")
        
        if critical_security:
            print("\n🚨 CRITICAL SECURITY RISKS:")
            for element_name, issues in critical_security:
                print(f"  - {element_name}() - {' + '.join(issues)}")
        
        if high_security:
            print("\n⚠️  HIGH SECURITY RISKS:")
            for element_name, issues in high_security:
                print(f"  - {element_name}() - {' + '.join(issues)}")
        
        if medium_security:
            print("\n🔶 MEDIUM SECURITY RISKS:")
            for element_name, issues in medium_security:
                print(f"  - {element_name}() - {' + '.join(issues)}")
        
        if security_recommendations:
            print("\n💡 SECURITY RECOMMENDATIONS:")
            for i, recommendation in enumerate(sorted(security_recommendations), 1):
                print(f"{i}. {recommendation}")
    
    elif security_check:
        print("\n🔒 SECURITY ANALYSIS: No security risks detected.")

def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(description='Analyze codebase for testing and documentation gaps')
    parser.add_argument('--fix-docs', action='store_true', 
                       help='Automatically generate documentation for functions with no docs')
    parser.add_argument('--api-only', action='store_true',
                       help='Scan only for API endpoints (Flask/FastAPI/Express routes)')
    parser.add_argument('--security-check', action='store_true',
                       help='Perform security analysis for financial, auth, and crypto functions')
    
    args = parser.parse_args()
    
    scan_codebase(fix_docs=args.fix_docs, api_only=args.api_only, security_check=args.security_check)

if __name__ == "__main__":
    main()