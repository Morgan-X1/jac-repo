# Codebase Genius

**Codebase Genius** is an AI-powered, agentic repository documentation generator built with Jac and Python. It automatically analyzes any public GitHub repository and produces comprehensive, structured Markdown documentation—complete with code context graphs, file trees, component explanations, and Mermaid diagrams.

---

## Features

- **Automated Repository Analysis**: Clone any GitHub repo, parse source files (Python, Jac, JavaScript, Rust), and extract functions, classes, walkers, and nodes.
- **AI-Powered Summaries**: Uses Google Gemini to generate concise README summaries and explain Jac components (walkers, nodes).
- **Code Context Graph (CCG)**: Builds a graph of entities and their relationships, visualized with Mermaid diagrams.
- **Structured Markdown Reports**: Outputs clean, organized documentation with:
  - Repository overview
  - File tree
  - Code Context Graph with stats and diagrams
  - Detailed parsed source information
- **Interactive Streamlit UI**: Enter a GitHub URL in a web interface and download the generated report.
- **Command-Line Interface**: Run the Jac pipeline interactively or pipe in a repo URL for non-interactive use.

---

## Project Structure

```
genius/
├── main.jac              # Jac orchestration: walkers and entry point
├── utils.py              # Python utilities: cloning, parsing, Gemini integration, markdown generation
├── parser_engine.py      # Multi-language parser (Python, Jac, JS, Rust)
├── ccg_builder.py        # Code Context Graph builder and Mermaid diagram generator
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (GOOGLE_API_KEY)
├── output/
│   └── app.py            # Streamlit web frontend
└── gen/                  # Python virtual environment
```

---

## Setup

### Prerequisites

- **Python 3.10+**
- **Git**
- **Jac** (installed via `jaclang`)
- **Google Gemini API Key** (for AI summaries and explanations)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/genius.git
   cd genius
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv gen
   source gen/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API key**:
   Create a `.env` file in the project root:
   ```bash
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

---

## Usage

### step 1: Command-Line (Jac)

Run the Jac pipeline interactively:

```bash
jac serve main.jac
```
open a new terminal 
### step 2: Streamlit Web UI

Launch the Streamlit frontend:

```bash
streamlit run app.py
```

Then:
1. Open the URL printed by Streamlit (e.g., `http://localhost:8501`)
2. Enter a GitHub repository URL
3. Click **Generate Documentation**
4. View and download the generated Markdown report

The app will display:
- The full Markdown report
- Rendered Mermaid diagrams
- A download button for the `.md` file

---

## How It Works

1. **Repository Cloning**: Uses `git clone` to fetch the target repository into a temporary directory.
2. **README Summarization**: Reads the README and generates a concise summary via Google Gemini.
3. **File Tree Construction**: Walks the repository and identifies source files (`.py`, `.jac`, `.js`, `.rs`, etc.).
4. **Source Parsing**: Extracts functions, classes, walkers, nodes, and other entities from each file using language-specific parsers.
5. **Component Explanation**: Sends identified Jac components to Gemini for natural-language explanations.
6. **Code Context Graph (CCG)**: Builds a graph of entities and their relationships; generates Mermaid diagrams.
7. **Markdown Generation**: Assembles all data into a structured Markdown report and writes it to `output/repo_summary.md`.

---

## Example Output

A generated report includes:

- **Overview**: AI-generated summary of the repository
- **Conceptual Agent Flow Diagram**: High-level Mermaid flowchart
- **File Tree**: List of source directories and files
- **Code Context Graph**: Stats (nodes, edges, connections) and a Mermaid diagram of code relationships
- **Parsed Source Details**: Breakdown of functions, classes, walkers, and nodes per file, with explanations

---

## Dependencies

See [`requirements.txt`](requirements.txt) for the full list. Key dependencies:

- `jaclang` – Jac language runtime
- `jac-cloud` – Jac cloud utilities
- `google-generativeai` – Gemini API client
- `streamlit` – Web UI framework
- `tree-sitter` – Language parsing library
- `byllm` – LLM integration utilities
- `requests` – HTTP library

---

## Configuration

### Environment Variables

- **`GOOGLE_API_KEY`**: Your Google Gemini API key (required for summaries and explanations)

### Jac Configuration

- **Entry Point**: `main.jac`
- **Walkers**:
  - `start_analysis`: Entry walker that prompts for a repo URL and spawns the analysis agent
  - `RepositoryAnalysisAgent`: Executes the full pipeline (clone → parse → summarize → build CCG → generate markdown)

### Python Utilities

- **`utils.py`**: Core functions for cloning, reading, summarizing, and markdown generation
- **`parser_engine.py`**: Multi-language parsers
- **`ccg_builder.py`**: Graph construction and Mermaid diagram generation

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'utils'`

Ensure you're running from the project root and that `sys.path` includes the root directory. The Streamlit app (`output/app.py`) automatically adjusts `sys.path`.

### `jac serve main.jac` fails

The current `main.jac` is designed for CLI execution (`jac run`), not as a web service. For web serving, use the Streamlit frontend (`streamlit run output/app.py`).

### Gemini API errors

- Verify your `GOOGLE_API_KEY` is set in `.env`
- Ensure the model name is correct (currently using `gemini-2.5-flash` for summaries and `gemini-2.0-flash-exp` for explanations)
- Check API quotas and network connectivity

### Streamlit not found

If you see `command not found: streamlit`, ensure it's installed in your virtual environment:

```bash
pip install streamlit
```

---

## Roadmap

- [ ] Add support for more languages (TypeScript, Go, Java)
- [ ] Implement caching to avoid re-processing the same repos
- [ ] Add CLI arguments for output path and model selection
- [ ] Integrate with Claude API for multi-LLM support
- [ ] Deploy Streamlit app to a cloud platform (Streamlit Cloud, AWS, GCP)
- [ ] Generate visual dependency graphs and call hierarchies
- [ ] Add unit tests for parsers and CCG builder

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **Jac Language**: For the agentic orchestration framework
- **Google Gemini**: For AI-powered summaries and explanations
- **Streamlit**: For the interactive web UI
- **Tree-sitter**: For language parsing

---

## Contact

For questions, issues, or feature requests, please open an issue on [GitHub](https://github.com/yourusername/genius/issues).

---

**Happy documenting! 🚀📚**
