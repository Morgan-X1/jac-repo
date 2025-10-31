import os
import subprocess
import tempfile
import shutil
import re
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from parser_engine import parse_source_file
from ccg_builder import build_code_context_graph, generate_mermaid_diagram as generate_ccg_mermaid

# Load environment variables from a .env file
load_dotenv()

def configure_gemini():
    """
    Configures the Gemini API client using the environment variable GOOGLE_API_KEY.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY environment variable is NOT set. Check your .env file.")
        raise EnvironmentError("GOOGLE_API_KEY not set in environment or .env file")
    
    # Use the retrieved API key for configuration
    genai.configure(api_key=api_key)
    print("SUCCESS: GOOGLE_API_KEY loaded and Gemini configured.")

def summarize_with_gemini(text, model_name="gemini-2.5-flash"):
    """
    Generates a concise summary of the provided text using the Gemini model.
    """
    try:
        configure_gemini()
        model = genai.GenerativeModel(model_name)
        # Limit text to 2000 chars to avoid very large API calls for summary
        prompt = f"Summarize this README into a concise 3-5 sentence overview:\n\n{text[:2000]}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"ERROR: Gemini summary failed. Ensure your GOOGLE_API_KEY is valid. Details: {e}"

def explain_jac_components_with_gemini(components_data, repo_name, model_name="gemini-2.0-flash-exp"):
    """
    Asks Gemini to explain the purpose of the identified JAC walkers and nodes
    based on their names and repository context.
    components_data is a list of {"name": str, "type": "Walker" or "Node", "path": str}
    """
    if not components_data:
        return {}

    configure_gemini()
    model = genai.GenerativeModel(model_name)

    component_list_str = ""
    for comp in components_data:
        component_list_str += f"- {comp['type']}: {comp['name']} (in {comp['path']})\n"

    system_prompt = (
        f"You are a professional software architect analyzing the '{repo_name}' repository. "
        "Your task is to provide a concise, 1-2 sentence explanation for the likely purpose of each listed JAC component (Walker or Node) based solely on its name and file location. "
        "Respond with a numbered list where each line starts with the component name, followed by a colon and the explanation."
    )
    
    user_query = f"Provide explanations for the following JAC components:\n\n{component_list_str}"

    print("Requesting explanations from Gemini...")

    try:
        # Some SDK versions don't support system_instruction; prepend system text.
        combined_prompt = system_prompt + "\n\n" + user_query
        response = model.generate_content(combined_prompt)
        
        # Parse the structured response from Gemini
        explanations = {}
        for line in response.text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Use regex to find "Name: Explanation" or "1. Name: Explanation"
            match = re.search(r'(?:^\d+\.\s*|^\s*)([a-zA-Z0-9_]+):\s*(.*)', line)
            if match:
                name = match.group(1).strip()
                explanation = match.group(2).strip()
                explanations[name] = explanation
        
        return explanations
    except Exception as e:
        print(f"ERROR: Failed to get component explanations from Gemini: {e}")
        return {}


def clone_repo(url):
    """
    Clones a Git repository to a temporary directory.
    """
    if not url.endswith('.git'):
        url += '.git'
    temp_dir = tempfile.mkdtemp(prefix='repo_')
    
    # Use Path to get the name reliably across OSs
    repo_name = Path(url).stem.replace('.git', '')

    try:
        print(f"Cloning {url} into {temp_dir}...")
        subprocess.run(['git', 'clone', '--depth', '1', url, temp_dir], check=True, capture_output=True)
        return temp_dir, repo_name
    except subprocess.CalledProcessError as e:
        # Clean up directory on failure
        shutil.rmtree(temp_dir)
        error_output = e.stderr.decode('utf-8', errors='ignore').strip()
        raise ValueError(f"Failed to clone repo '{url}'. Error: {error_output}")

def build_file_tree(repo_path):
    """
    Walks the repository and builds a list of source files to process.
    """
    result = []
    # Directories to ignore
    ignore_dirs = ['.git', 'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build']
    
    for root, dirs, files in os.walk(repo_path):
        # Modify dirs in-place to prune traversal
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        rel_root = os.path.relpath(root, repo_path)
        # File extensions to consider as source code
        src_files = [f for f in files if f.endswith(('.py', '.jac', '.js', '.rs', '.ts', '.jsx', '.tsx'))]
        
        if src_files:
            result.append({'dir': rel_root if rel_root != '.' else '.', 'files': src_files})
    return result

def read_readme(repo_path):
    """
    Reads the primary README file from the repository.
    """
    for name in ['README.md', 'readme.md', 'README.txt', 'Readme.md']:
        path = os.path.join(repo_path, name)
        if os.path.isfile(path):
            print(f"Reading {name}...")
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except IOError as e:
                print(f"Warning: Could not read {name}. {e}")
                return 'No README found.'
    return 'No README found.'

def write_md(output_path, md_content):
    """
    Writes the Markdown summary content to the specified output path.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

def generate_mermaid_diagram(parsed_files):
    """
    Generates a conceptual Mermaid flow diagram based on identified Walkers (agents).
    """
    # Collect all walkers and filter to unique, non-Python ones (assuming agents are walkers)
    all_walkers = set()
    for pf in parsed_files:
        if pf.get('type') == 'jac':
            for w_tuple in pf.get('walkers', []):
                # Handle both string names and (name, explanation) tuples
                w_name = w_tuple[0] if isinstance(w_tuple, tuple) else w_tuple
                all_walkers.add(w_name)

    walkers_list = sorted(list(all_walkers))
    
    if not walkers_list:
        return ""

    # Define the known agent flow based on the project description
    # RepoMapper -> CodeAnalyzer -> DocGenie
    
    mermaid_content = "```mermaid\nflowchart TD\n"
    
    # 1. Define the Start/Entry Point
    mermaid_content += "  A[Input URL] --> B{Trigger: gen_docs Walker};\n"
    
    # 2. Define the main Agent flow
    mermaid_content += "  B --> C(RepoMapper);\n"
    mermaid_content += "  C --> D(CodeAnalyzer);\n"
    mermaid_content += "  D --> E(DocGenie);\n"
    
    # 3. Define the Output
    mermaid_content += "  E --> F[Output: Markdown Report];\n"
    
    mermaid_content += "```"
    
    return mermaid_content

def summarize_repo(repo_url, output_md_path):
    """
    Main function to clone, summarize, parse, and generate the report.
    """
    repo_path = None
    try:
        repo_path, repo_name = clone_repo(repo_url)
        readme = read_readme(repo_path)
        
        print("Generating Gemini summary...")
        
        # --- Check for 'No README found.' before calling Gemini ---
        if readme.strip() == 'No README found.':
            summary = "No standard README file (e.g., README.md) was found in the repository root for summarization."
        else:
            summary = summarize_with_gemini(readme)
        # -----------------------------------------------------------------
        
        print("Building file tree and parsing files...")
        file_tree = build_file_tree(repo_path)
        parsed_files = []
        
        for entry in file_tree:
            for fname in entry['files']:
                full_path = os.path.join(repo_path, entry['dir'], fname)
                parsed = parse_source_file(full_path)
                parsed['path'] = os.path.join(entry['dir'] if entry['dir'] != '.' else '', fname)
                # Initialize walkers/nodes as lists of strings before enrichment
                if parsed.get('type') == 'jac':
                    parsed['walkers'] = [(w) for w in parsed.get('walkers', [])]
                    parsed['nodes'] = [(n) for n in parsed.get('nodes', [])]
                parsed_files.append(parsed)

        # 1. Collect all JAC components for explanation
        jac_components_to_explain = []
        for pf in parsed_files:
            if pf.get('type') == 'jac':
                path = pf['path']
                # Walkers and nodes are lists of strings after initial parse
                for w in pf.get('walkers', []):
                    jac_components_to_explain.append({"name": w, "type": "Walker", "path": path})
                for n in pf.get('nodes', []):
                    jac_components_to_explain.append({"name": n, "type": "Node", "path": path})

        # 2. Get explanations from Gemini
        explanations_dict = explain_jac_components_with_gemini(jac_components_to_explain, repo_name)
        
        # 3. Enrich parsed_files with explanations (converting names to tuples (name, explanation))
        for pf in parsed_files:
            if pf.get('type') == 'jac':
                
                def attach_explanation(component_list):
                    new_list = []
                    for name in component_list:
                        explanation = explanations_dict.get(name, "Explanation could not be generated.")
                        new_list.append((name, explanation))
                    return new_list

                pf['walkers'] = attach_explanation(pf.get('walkers', []))
                pf['nodes'] = attach_explanation(pf.get('nodes', []))

        # Generate conceptual agent flow diagram (high-level, not CCG)
        diagram = generate_mermaid_diagram(parsed_files)

        # Build Code Context Graph (CCG) from parsed files
        # Prepare CCG-safe copy (ensure walkers/nodes are plain strings)
        ccg_input_files = []
        for pf in parsed_files:
            ccg_pf = dict(pf)
            if ccg_pf.get('type') == 'jac':
                # Convert (name, explanation) tuples back to names for CCG
                ccg_pf['walkers'] = [w[0] if isinstance(w, tuple) else w for w in ccg_pf.get('walkers', [])]
                ccg_pf['nodes'] = [n[0] if isinstance(n, tuple) else n for n in ccg_pf.get('nodes', [])]
            ccg_input_files.append(ccg_pf)

        ccg_result = build_code_context_graph(ccg_input_files)
        ccg_stats = ccg_result.get('stats', {})
        # Produce a Mermaid diagram from the CCG
        ccg_mermaid = generate_ccg_mermaid(ccg_result)

        # --- Generate Markdown Report ---
        md = f"# Repo Summary: {repo_name}\n\n"
        md += f"## Overview\n{summary}\n\n"
        
        # Add Diagram Section
        if diagram:
            md += "## Conceptual Agent Flow Diagram\n"
            md += diagram
            md += "\n"
        
        # File Tree Section
        md += "## File Tree\n"
        for entry in file_tree:
            dir_name = entry['dir'] if entry['dir'] != '.' else 'root'
            md += f"- `{dir_name}`: {', '.join(entry['files'])}\n"
        md += "\n"
        
        # CCG Section
        md += "## Code Context Graph\n"
        if ccg_stats:
            md += (
                f"- Nodes: {ccg_stats.get('node_count', 0)} | "
                f"Edges: {ccg_stats.get('edge_count', 0)} | "
                f"Files: {ccg_stats.get('file_count', 0)} | "
                f"Avg connections: {round(ccg_stats.get('avg_connections', 0.0), 2)}\n\n"
            )
        if ccg_mermaid:
            md += "### Code Graph (Mermaid)\n"
            md += "```mermaid\n" + ccg_mermaid + "\n```\n\n"

    # Parsed Source Section
        md += "## Parsed Source Details\n"
        
        # Helper function to format lists for Markdown (updated for explanation tuples)
        def format_list_with_explanations(items):
            formatted = []
            for item in items:
                # Items are now expected to be (name, explanation) tuples for JAC files
                if isinstance(item, tuple) and len(item) == 2:
                    name, explanation = item
                    formatted.append(f'`{name}`: {explanation}')
                else:
                    # Fallback for simple names (e.g., Python functions)
                    formatted.append(f'`{item}`')
            return '\n  - '.join(formatted) if formatted else 'None'
            
        for pf in parsed_files:
            md += f"### `{pf['path']}`\n"
                
            if pf['type'] == 'python':
                # For Python, use the original formatting for brevity
                md += f"- Functions: {', '.join([f'`{f}`' for f in pf.get('funcs', [])]) or 'None'}\n"
                md += f"- Classes: {', '.join([f'`{c}`' for c in pf.get('classes', [])]) or 'None'}\n"
            elif pf['type'] == 'jac':
                md += f"- Walkers:\n  - {format_list_with_explanations(pf.get('walkers', []))}\n"
                md += f"- Nodes:\n  - {format_list_with_explanations(pf.get('nodes', []))}\n"
            elif pf['type'] in ['javascript', 'typescript']:
                # For JS/TS, use the original formatting for brevity
                md += f"- Functions: {', '.join([f'`{f}`' for f in pf.get('funcs', [])]) or 'None'}\n"
                md += f"- Classes: {', '.join([f'`{c}`' for c in pf.get('classes', [])]) or 'None'}\n"
            elif pf['type'] == 'rust':
                # For Rust, use the original formatting for brevity
                md += f"- Functions: {', '.join([f'`{f}`' for f in pf.get('funcs', [])]) or 'None'}\n"
                md += f"- Structs: {', '.join([f'`{s}`' for s in pf.get('structs', [])]) or 'None'}\n"
                md += f"- Enums: {', '.join([f'`{e}`' for e in pf.get('enums', [])]) or 'None'}\n"
            elif pf.get('error'):
                md += f"- Error: {pf['error']}\n"
            else:
                # Fallback for unknown file types
                content_preview = pf.get('content', '')[:200].replace('\n', ' ').strip()
                md += f"- Type: {pf['type']} | Content Preview: {content_preview}...\n"
            md += "\n"

        write_md(output_md_path, md)
        return output_md_path

    except Exception as e:
        print(f"\nFATAL ERROR during processing: {e}")
        return f"Failed to generate summary due to a fatal error: {e}"
    finally:
        if repo_path and os.path.isdir(repo_path):
            print(f"Cleaning up temporary directory: {repo_path}")
            shutil.rmtree(repo_path)


def summarize_repo_default(repo_url):
    """
    Convenience wrapper for Jac: generates markdown to a default path and returns the path.
    """
    output_path = "output/repo_summary.md"
    return summarize_repo(repo_url, output_path)


def prompt_repo_url(prompt: str = "Enter GitHub repository URL: ") -> str:
    """
    Prompt the user for a repository URL via stdin and return a trimmed string.
    Returns an empty string if stdin is closed or no input is provided.
    """
    try:
        return input(prompt).strip()
    except EOFError:
        return ""
 
