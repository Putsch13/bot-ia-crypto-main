import os
import re

COMPONENTS = [
    "ActiveTradesPanel.jsx",
    "DashboardPerf.jsx",
    "HistoryPanel.jsx",
    "IAReportLive.jsx",
    "LogPanel.jsx",
    "TopFlopCards.jsx"
]

BASE_PATH = "src/components"

def patch_file(filename):
    full_path = os.path.join(BASE_PATH, filename)
    if not os.path.exists(full_path):
        print(f"⛔ Fichier non trouvé : {full_path}")
        return

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remplace x.toFixed(...) => (x ?? 0).toFixed(...)
    patched = re.sub(r"([a-zA-Z0-9_\.]+)\.toFixed\((\d)\)", r"(\1 ?? 0).toFixed(\2)", content)

    if content != patched:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(patched)
        print(f"✅ Patch appliqué : {filename}")
    else:
        print(f"🔍 Aucun changement : {filename}")

if __name__ == "__main__":
    for comp in COMPONENTS:
        patch_file(comp)
