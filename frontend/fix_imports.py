import os
import re

FILES = [
    "app/cameras/[id]/page.tsx",
    "app/cenarios/[id]/page.tsx",
    "app/eventos/[id]/page.tsx",
    "app/localizacoes/[id]/page.tsx",
    "app/pessoas/[id]/page.tsx",
    "app/pessoa-eventos/[id]/page.tsx",
    "app/pessoa-eventos/page.tsx",
]

for file_path in FILES:
    if not os.path.exists(file_path):
        continue
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Fix the missing '}' issue in the imports
    content = content.replace(", getUsuarioLocal  from", ", getUsuarioLocal } from")
    content = content.replace(", ShieldAlert  from", ", ShieldAlert } from")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Fixed {file_path}")
