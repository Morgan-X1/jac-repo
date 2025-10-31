import os
import re
import sys
import json
import traceback
import requests
import streamlit as st

# Ensure repository root is on sys.path so we can import `utils.py` from the project root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT_DIR not in sys.path:
	sys.path.insert(0, ROOT_DIR)

# We will call the Jac API server instead of running utils directly


st.set_page_config(page_title="Codebase Genius - Repo Docs", layout="wide")

st.title("📚 Morgan Codebase Genius — Repository Documentation Generator ")
st.write(
	"Enter a public GitHub repository URL and generate a structured Markdown report with overview, file tree, code context graph, and more."
)


def render_mermaid_diagram(mermaid_code: str, height: int = 600):
	"""Render a Mermaid diagram in Streamlit using an HTML component."""
	# Basic safety: escape backticks in code block to avoid breaking template
	safe_code = mermaid_code.replace("`", "\u0060")
	html = f"""
	<html>
	<head>
	  <meta charset='utf-8'/>
	  <script type="module">
		import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
		mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
	  </script>
	  <style>
		body {{ margin: 0; padding: 0; }}
		.container {{ padding: 8px; }}
	  </style>
	</head>
	<body>
	  <div class="container">
		<div class="mermaid">{safe_code}</div>
	  </div>
	</body>
	</html>
	"""
	st.components.v1.html(html, height=height, scrolling=True)


def extract_mermaid_blocks(md_text: str):
	"""Return a list of strings for all ```mermaid ... ``` blocks in the markdown."""
	pattern = re.compile(r"```mermaid\s+([\s\S]*?)```", re.MULTILINE)
	return [m.group(1).strip() for m in pattern.finditer(md_text or "")] 


# --- Sidebar: API server & credentials ---
st.sidebar.header("Server Settings")
default_base = os.getenv("JAC_API_BASE", "http://localhost:8000")
base_url = st.sidebar.text_input("API Base URL", value=default_base)
email = st.sidebar.text_input("Email", value=os.getenv("JAC_API_EMAIL", "test@mail.com"))
password = st.sidebar.text_input("Password", value=os.getenv("JAC_API_PASSWORD", "password"), type="password")

if "token" not in st.session_state:
	st.session_state.token = None

def login_or_register(_base: str, _email: str, _password: str) -> str | None:
	try:
		r = requests.post(f"{_base}/user/login", json={"email": _email, "password": _password}, timeout=15)
		if r.status_code == 200:
			return r.json().get("token")
		# Try register then login
		rr = requests.post(f"{_base}/user/register", json={"email": _email, "password": _password}, timeout=15)
		if rr.status_code in (200, 201):
			r2 = requests.post(f"{_base}/user/login", json={"email": _email, "password": _password}, timeout=15)
			if r2.status_code == 200:
				return r2.json().get("token")
		return None
	except Exception:
		return None

if st.sidebar.button("Connect / Refresh Token"):
	tok = login_or_register(base_url, email, password)
	if tok:
		st.session_state.token = tok
		st.sidebar.success("Authenticated")
	else:
		st.sidebar.error("Failed to authenticate to API server")

with st.form("repo_form"):
	repo_url = st.text_input(
		"GitHub repository URL",
		placeholder="https://github.com/owner/repo.git",
	)
	submitted = st.form_submit_button("Generate Documentation via API")

if submitted:
	if not repo_url.strip():
		st.error("Please enter a valid GitHub repository URL.")
	else:
		if not st.session_state.token:
			st.error("Not authenticated. Click 'Connect / Refresh Token' in the sidebar first.")
		else:
			with st.spinner("Processing repository on server — cloning, parsing, summarizing, and building graphs…"):
				try:
					resp = requests.post(
						f"{base_url}/walker/start_analysis",
						headers={"Authorization": f"Bearer {st.session_state.token}"},
						json={"target_url": repo_url.strip()},
						timeout=600,
					)
				except Exception as e:
					st.error("Request to API failed.")
					st.exception(e)
				else:
					if resp.status_code != 200:
						st.error(f"Server error ({resp.status_code}).")
						st.text(resp.text)
					else:
						try:
							payload = resp.json()
						except Exception:
							st.error("Invalid JSON response from server.")
							st.text(resp.text)
						else:
							reports = payload.get("reports", [])
							report = reports[0] if reports else {}
							md_path = report.get("markdown_path")
							status = report.get("status", "unknown")
							repo_name = report.get("repository", "")

							if status != "complete" or not md_path:
								st.error("Analysis did not complete or no markdown path returned.")
								st.json(report)
							else:
								st.success(f"{repo_name}: Markdown generated at {md_path}")
								md_text = None
								if isinstance(md_path, str) and os.path.isfile(md_path):
									with open(md_path, "r", encoding="utf-8") as f:
										md_text = f.read()
								else:
									st.info("Markdown file not found locally. Showing path returned by server.")

								if md_text:
									st.download_button(
										label="Download Markdown",
										data=md_text,
										file_name=os.path.basename(md_path),
										mime="text/markdown",
									)
									st.markdown("---")
									st.subheader("📄 Report Preview")
									st.markdown(md_text)

									mermaids = extract_mermaid_blocks(md_text)
									if mermaids:
										st.markdown("---")
										st.subheader("🧭 Diagrams")
										for i, code in enumerate(mermaids, start=1):
											st.caption(f"Mermaid Diagram #{i}")
											render_mermaid_diagram(code, height=650)
									else:
										st.info("No Mermaid diagrams found in the report.")

st.markdown("""
> Tips:
> - Ensure your GOOGLE_API_KEY is set on the server running `jac serve`.
> - Click "Connect / Refresh Token" in the sidebar before generating documentation.
> - API Base URL defaults to http://localhost:8000. Update it if your server runs elsewhere.
""")

