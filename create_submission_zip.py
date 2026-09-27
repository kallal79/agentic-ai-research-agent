import os
import zipfile

def create_submission_zip():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(base_dir, "agentic_ai_assignment_kallal_mukherjee.zip")
    
    exclude_dirs = {"venv", ".git", ".pytest_cache", "__pycache__"}
    exclude_exts = {".pyc", ".pyo", ".zip"}
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in exclude_exts or file.endswith(".zip"):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_dir)
                zipf.write(full_path, rel_path)
                
    print(f"Created submission ZIP: {zip_path}")
    print(f"Size: {os.path.getsize(zip_path)} bytes")

if __name__ == "__main__":
    create_submission_zip()
