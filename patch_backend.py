import re
import os

files_to_patch = [
    "backend/routes/camera_routes.py",
    "backend/routes/scenario_routes.py",
    "backend/routes/event_routes.py",
    "backend/routes/location_routes.py",
    "backend/routes/person_routes.py",
    "backend/routes/person_event_routes.py",
    "backend/routes/upload_mapa_route.py"
]

for fp in files_to_patch:
    if not os.path.exists(fp):
        print(f"Skipping {fp}")
        continue
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Add imports if not present
    if "apenas_admin" not in content:
        content = re.sub(
            r'(from fastapi import [^\n]+)',
            r'\1\nfrom backend.services.auth_dependency import apenas_admin',
            content,
            count=1
        )
        
    # Make sure Depends is imported
    if "Depends" not in content:
        content = re.sub(r'(from fastapi import )', r'\1Depends, ', content, count=1)
    
    def replacer(m):
        inner = m.group(2)
        if "dependencies=" in inner:
            if "apenas_admin" not in inner:
                inner = inner.replace("dependencies=[", "dependencies=[Depends(apenas_admin), ")
        else:
            if inner:
                inner += ", dependencies=[Depends(apenas_admin)]"
            else:
                inner = "dependencies=[Depends(apenas_admin)]"
        return f"@router.{m.group(1)}({inner})"

    # we use re.DOTALL in case it's multiline?
    # Usually @router.post("/xxx") is single line. If it spans multiple lines, we need DOTALL or modify the regex.
    # Let's handle multi-line inside parenthesis just in case
    content = re.sub(r'@router\.(post|put|delete)\((.*?)\)', replacer, content, flags=re.DOTALL)

    with open(fp, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Patched {fp}")
