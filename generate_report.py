import os

project_root = os.path.abspath(os.path.dirname(__file__))
output_path = os.path.join(project_root, "informe.txt")

TARGET_FOLDERS = ["core", "gui"]
EXCLUDE_DIRS = {"__pycache__"}

with open(output_path, "w", encoding="utf-8") as out_file:
    for target in TARGET_FOLDERS:
        target_path = os.path.join(project_root, target)
        if not os.path.isdir(target_path):
            out_file.write(f"[Carpeta no encontrada: {target}]\n\n")
            continue

        for root, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            rel_root = os.path.relpath(root, project_root)
            out_file.write(f"\n{'='*60}\n")
            out_file.write(f"# Carpeta: {rel_root}\n")
            out_file.write(f"{'='*60}\n\n")

            for f in sorted(files):
                file_path = os.path.join(root, f)
                rel_file = os.path.relpath(file_path, project_root)
                out_file.write(f"## Archivo: {rel_file}\n")
                out_file.write(f"{'-'*60}\n")
                try:
                    with open(file_path, "r", encoding="utf-8") as fin:
                        content = fin.read()
                    out_file.write(content)
                except Exception as e:
                    out_file.write(f"[Error al leer el archivo: {e}]")
                out_file.write("\n\n")

print(f"Informe generado en: {output_path}")
