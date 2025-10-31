"""
Improved Parser Engine
Parses source files and extracts structure + content for CCG building
"""

import ast
import re
from pathlib import Path


def parse_python(file_path):
    """Parse Python files using AST"""
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    try:
        tree = ast.parse(code)
        funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        
        # Extract imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return {
            'type': 'python',
            'funcs': funcs,
            'classes': classes,
            'imports': imports,
            'content': code  # Important for CCG relationship detection
        }
    except SyntaxError as e:
        return {
            'type': 'python',
            'error': f'Parse error: {str(e)}',
            'funcs': [],
            'classes': [],
            'imports': [],
            'content': code
        }


def parse_javascript(file_path):
    """Parse JavaScript files using regex"""
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # Function patterns
    funcs = re.findall(r'\bfunction\s+(\w+)', code)
    arrow_funcs = re.findall(r'\bconst\s+(\w+)\s*=\s*\([^)]*\)\s*=>', code)
    funcs.extend(arrow_funcs)
    
    # Class pattern
    classes = re.findall(r'\bclass\s+(\w+)', code)
    
    # Import patterns
    imports = re.findall(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', code)
    imports.extend(re.findall(r'require\([\'"]([^\'"]+)[\'"]\)', code))
    
    return {
        'type': 'javascript',
        'funcs': list(set(funcs)),
        'classes': list(set(classes)),
        'imports': list(set(imports)),
        'content': code
    }


def parse_rust(file_path):
    """Parse Rust files using regex"""
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    funcs = re.findall(r'\bfn\s+(\w+)', code)
    structs = re.findall(r'\bstruct\s+(\w+)', code)
    enums = re.findall(r'\benum\s+(\w+)', code)
    traits = re.findall(r'\btrait\s+(\w+)', code)
    
    # Use statements
    imports = re.findall(r'use\s+([^;]+);', code)
    
    return {
        'type': 'rust',
        'funcs': list(set(funcs)),
        'structs': list(set(structs)),
        'enums': list(set(enums)),
        'traits': list(set(traits)),
        'imports': imports,
        'content': code
    }


def parse_jac(file_path):
    """Parse Jac files using improved regex"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Match node/walker followed by name, then optional whitespace and { or :
    walkers = re.findall(r'\bwalker\s+(\w+)\s*[{:]?', content)
    nodes = re.findall(r'\bnode\s+(\w+)\s*[{:]?', content)
    
    # Match enums
    enums = re.findall(r'\benum\s+(\w+)\s*[{:]?', content)
    
    # Match abilities (can methods)
    abilities = re.findall(r'\bcan\s+(\w+)\s+with', content)
    
    # Match global variables
    globals_vars = re.findall(r'\bglob\s+(\w+)\s*=', content)
    
    # Match imports (Jac style)
    imports = re.findall(r'import:py\s+from\s+(\w+)', content)
    imports.extend(re.findall(r'import:jac\s+from\s+(\w+)', content))
    imports.extend(re.findall(r'import\s+from\s+[\w.]+\s*{\s*([^}]+)\s*}', content))
    
    # Match edges
    edges = re.findall(r'\bedge\s+(\w+)', content)
    
    return {
        'type': 'jac',
        'walkers': list(set(walkers)),
        'nodes': list(set(nodes)),
        'enums': list(set(enums)),
        'abilities': list(set(abilities)),
        'globals': list(set(globals_vars)),
        'edges': list(set(edges)),
        'imports': imports,
        'content': content
    }


def parse_generic(file_path):
    """Parse generic/unknown files"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return {
        'type': 'unknown',
        'content': content[:500]
    }


def parse_source_file(file_path):
    """
    Parse a source file and return structured data
    
    Args:
        file_path: Path to source file
        
    Returns:
        Dictionary with parsed data including:
        - type: file type (python, jac, javascript, rust)
        - funcs, classes, nodes, walkers, etc.
        - content: full file content (for relationship detection)
    """
    ext = Path(file_path).suffix
    
    try:
        if ext == '.py':
            return parse_python(file_path)
        elif ext == '.js':
            return parse_javascript(file_path)
        elif ext == '.rs':
            return parse_rust(file_path)
        elif ext == '.jac':
            return parse_jac(file_path)
        else:
            return parse_generic(file_path)
    except Exception as e:
        return {
            'type': 'error',
            'error': str(e),
            'content': ''
        }


if __name__ == "__main__":
    # Test the parser
    import sys
    
    if len(sys.argv) > 1:
        result = parse_source_file(sys.argv[1])
        print(f"File: {sys.argv[1]}")
        print(f"Type: {result.get('type')}")
        
        if result.get('funcs'):
            print(f"Functions: {result['funcs']}")
        if result.get('classes'):
            print(f"Classes: {result['classes']}")
        if result.get('nodes'):
            print(f"Nodes: {result['nodes']}")
        if result.get('walkers'):
            print(f"Walkers: {result['walkers']}")
        if result.get('imports'):
            print(f"Imports: {result['imports'][:5]}...")  # First 5
    else:
        print("Usage: python parser_engine.py <file_path>")