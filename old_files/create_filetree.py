import os

def create_file(filepath, content=""):
    """Creates a file with optional content."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def create_project_structure(base_dir="ent-cpt-agent"):
    """Creates the required directory and file structure."""
    structure = {
        "": ["README.md", "requirements.txt", "setup.py", "config.json"],
        "data": ["CPT codes for ENT.xlsx"],
        "src": ["__init__.py"],
        "src/agent": ["__init__.py", "ent_cpt_agent.py", "cpt_database.py", "rules_engine.py"],
        "src/config": ["__init__.py", "agent_config.py"],
        "src/conversation": ["__init__.py", "conversation_manager.py"],
        "src/api": ["__init__.py", "api_interface.py"],
        "src/web": ["__init__.py", "web_ui.py"],
        "src/web/templates": ["index.html"],
        "scripts": ["install.sh", "run_server.sh"],
        "tests": ["__init__.py", "test_agent.py", "test_cpt_database.py", "test_rules_engine.py", "test_api.py"],
        "docs": ["installation.md", "usage_examples.md", "api_docs.md"],
        "conversations": []
    }
    
    for folder, files in structure.items():
        folder_path = os.path.join(base_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
        for file in files:
            create_file(os.path.join(folder_path, file))
    
    print(f"Project structure for '{base_dir}' created successfully.")

if __name__ == "__main__":
    create_project_structure()
