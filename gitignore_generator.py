
"""Generate .gitignore files for Python projects."""

GITIGNORE_TEMPLATES = {
    "Python": """# Python cache files
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/
""",
    "Virtual environments": """# Virtual environments
.venv/
venv/
env/
""",
    "pytest": """# Testing and coverage
.pytest_cache/
.coverage
.coverage.*
htmlcov/
""",
    "Jupyter Notebook": """# Jupyter Notebook
.ipynb_checkpoints/
""",
    "Streamlit": """# Streamlit secrets
.streamlit/secrets.toml
""",
    "Ruff": """# Ruff
.ruff_cache/
""",
    "VS Code": """# VS Code settings
.vscode/
""",
    "PyCharm": """# PyCharm
.idea/
""",
    "macOS": """# macOS
.DS_Store
""",
    "Windows": """# Windows
Thumbs.db
Desktop.ini
""",
}


def generate_gitignore(selected_options):
    """Generate .gitignore content from selected templates."""

    sections = []

    for option in dict.fromkeys(selected_options):
        if option not in GITIGNORE_TEMPLATES:
            raise ValueError(f"Unknown option: {option}")

        sections.append(GITIGNORE_TEMPLATES[option].strip())

    if not sections:
        return ""

    return "\n\n".join(sections) + "\n"
