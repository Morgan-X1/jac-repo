

import from utils { clone_repo, read_readme, build_file_tree, summarize_with_gemini, explain_jac_components_with_gemini, generate_mermaid_diagram, write_md, summarize_repo_default, prompt_repo_url }
import from parser_engine { parse_source_file }

node Repository {
    """Represents a repository and holds its metadata."""
    has url: str = "";
    has name: str = "";
    has local_path: str = "";
    has readme_summary: str = "";
    has files_to_analyze: list = [];  # List of paths
}

node AnalyzedFile {
    """Represents a source file after it has been parsed."""
    has path: str = "";
    has language: str = "";
    has parsed_data: dict = {};
    has components_explained: bool = False;
}


walker RepositoryAnalysisAgent {
    """
    Handles the entire analysis pipeline sequentially: cloning, mapping,
    parsing, CCG building, and reporting, operating directly on the Repository node.
    """
    
    can visit_repo with Repository entry {
        print(f"📥 Starting full analysis pipeline for: {here.url}");
        
       
        
        # 1. Call Python's clone_repo function
        repo_result = clone_repo(here.url);
        repo_path = repo_result[0];
        repo_name = repo_result[1];
        
        here.local_path = repo_path;
        here.name = repo_name;
        
        # 2. Call Python's read_readme function
        readme_content = read_readme(repo_path);
        # Summarize README via utils and store on the Repository node
        if readme_content and readme_content != "No README found." {
            summary = summarize_with_gemini(readme_content);
            here.readme_summary = summary;
            print(f"📝 README summary (first 2000 chars): {summary[:2000]}");
        } else {
            here.readme_summary = "No README found.";
        };
        
        # 3. Call Python's build_file_tree function
        file_tree = build_file_tree(repo_path);
        
        # Extract all file paths from the tree for later traversal
        all_files = [];
        for item in file_tree {
            for fname in item["files"] {
                path = (item["dir"] if item["dir"] != "." else "") + "/" + fname;
                all_files.append(path);
            };
        };
            here.files_to_analyze = all_files;
        
        print(f"✅ Cloning and mapping complete. Found {len(all_files)} files.");

        # --- PHASE 2: CODE PARSING (Data Generation) ---
            print(f"\n🔬 Starting code parsing for {here.name}");
        
        for file_path in here.files_to_analyze {
            full_path = here.local_path + "/" + file_path;

            # 1. Call Python's parse_source_file function
            parsed_data = parse_source_file(full_path);

            # 2. If parser reported an error, log and skip
            if parsed_data.get("type", "") == "error" or parsed_data.get("error") {
                print(f"  - ❌ Parse issue {file_path}: {parsed_data.get('error', 'unknown')}");
            } else {
                # 3. Create an AnalyzedFile node and connect it to the Repository
                here ++> AnalyzedFile(
                    path=file_path,
                    language=parsed_data.get("type", "unknown"),
                    parsed_data=parsed_data
                );
                print(f"  - Parsed: {file_path}");
            };
        };
        
    print(f"✅ All files processed. Starting enrichment stage.");

        # --- OPTIONAL ENRICHMENT: Explain Jac components via LLM ---
        components = [];
        for af_node in [-->](`?AnalyzedFile) {
            if af_node.parsed_data.get("type", "unknown") == "jac" {
                for w in af_node.parsed_data.get("walkers", []) {
                    components.append({"name": w, "type": "Walker", "path": af_node.path});
                };
                for n in af_node.parsed_data.get("nodes", []) {
                    components.append({"name": n, "type": "Node", "path": af_node.path});
                };
            };
        };
        if len(components) > 0 {
            print("🧠 Explaining Jac components via LLM...");
            expl = explain_jac_components_with_gemini(components, here.name);
            for af_node in [-->](`?AnalyzedFile) {
                walker_expls = [];
                for w in af_node.parsed_data.get("walkers", []) {
                    walker_expls.append({"name": w, "explanation": expl.get(w, "")});
                };
                node_expls = [];
                for n in af_node.parsed_data.get("nodes", []) {
                    node_expls.append({"name": n, "explanation": expl.get(n, "")});
                };
                af_node.parsed_data["walker_explanations"] = walker_expls;
                af_node.parsed_data["node_explanations"] = node_expls;
                af_node.components_explained = True;
            };
        };

        # --- REPORTING: Generate Markdown via utils (includes CCG now) ---
        md_path = summarize_repo_default(here.url);
        print(f"📝 Markdown written to: {md_path}");
        
        # --- OPTIONAL OUTPUT: Markdown summary + diagram ---
        pfs = [];
        for af_node in [-->](`?AnalyzedFile) {
            pfs.append({
                "type": af_node.parsed_data.get("type", "unknown"),
                "walkers": af_node.parsed_data.get("walkers", []),
                "nodes": af_node.parsed_data.get("nodes", []),
                "path": af_node.path
            });
        };
    

        # The final step is reporting the result
        report {
            "status": "complete",
            "repository": here.name,
            "markdown_path": md_path
        };
    }
}

# Helper walker to collect parsed file data
walker CollectParsedFiles {
    has collected_data: list = [];
    
    can collect with AnalyzedFile entry {
            self.collected_data.append(here.parsed_data);
    }
}



walker start_analysis {
    """
    API-callable walker to analyze a GitHub repository.
    Call via API with: {"target_url": "https://github.com/owner/repo.git"}
    """
    has target_url: str = "";
    
    can start with `root entry {
        if not self.target_url or self.target_url == "" {
            report {
                "status": "error",
                "message": "No target_url provided. Please include 'target_url' in your request."
            };
            return;
        };
        
        print(f"👉 start_analysis walker executing for: {self.target_url}");
        # Simplified API flow: delegate full processing to Python utils and return the markdown path
        md_path = summarize_repo_default(self.target_url);
        print(f"📝 Markdown written to: {md_path}");

        # Best-effort repository name from URL
        repo_name = self.target_url;
        if ".git" in repo_name {
            # crude trim for .git suffix
            repo_name = repo_name[:-4];
        };
        
        report {
            "status": "complete",
            "repository": repo_name,
            "markdown_path": md_path
        };
    }
}
