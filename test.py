import os

IGNORE_FOLDERS = {
    "venv", "__pycache__", ".vscode", "mlruns", "mlartifacts", "static",
    "shap_plot", "tmp", "jars", ".git", "postgres-data", "images",
    ".minio.sys", "warehouse", "mlflow-artifacts", "metadata"
}
IGNORE_FILES = {".DS_Store", ".env", "generate_tree.py", "architecture.png"}

INCLUDE_EXTENSIONS = {".py", ".yml", ".yaml"}
INCLUDE_FILENAMES = {"Dockerfile", "requirements.txt"}

IGNORE_EXTENSIONS = {".parquet", ".csv", ".json", ".txt", ".log", ".lock", ".iml", ".xml", ".md", ".avro", ".bin", ".png", ".html", ".pkl"}

# Folders to show but not expand deeper
SHALLOW_FOLDERS = {"data"}

def tree(dir_path, prefix="", shallow=False):
    if shallow:
        return

    entries = sorted(os.listdir(dir_path))

    filtered = []
    for entry in entries:
        if entry in IGNORE_FOLDERS or entry in IGNORE_FILES:
            continue
        path = os.path.join(dir_path, entry)
        ext = os.path.splitext(entry)[1]
        if os.path.isdir(path):
            filtered.append(entry)
        elif ext in IGNORE_EXTENSIONS:
            continue
        elif entry in INCLUDE_FILENAMES or ext in INCLUDE_EXTENSIONS:
            filtered.append(entry)

    pointers = ["├── "] * (len(filtered) - 1) + ["└── "]

    for pointer, entry in zip(pointers, filtered):
        path = os.path.join(dir_path, entry)
        print(prefix + pointer + entry)
        if os.path.isdir(path):
            extension = "│   " if pointer == "├── " else "    "
            is_shallow = entry in SHALLOW_FOLDERS
            tree(path, prefix + extension, shallow=is_shallow)

if __name__ == "__main__":
    tree(".")