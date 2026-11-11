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
    "app/parametros/[id]/page.tsx",
    "app/parametros/page.tsx"
]

for file_path in FILES:
    if not os.path.exists(file_path):
        print(f"Skipping {file_path}, does not exist")
        continue
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Skip if already has souAdmin (already protected)
    if "setSouAdmin" in content and "ShieldAlert" in content:
        print(f"Skipping {file_path}, already protected")
        continue

    # Add getUsuarioLocal to imports from @/lib/api if not present
    if "getUsuarioLocal" not in content:
        content = re.sub(r'(import \{[^}]*)\}( from "@/lib/api";?)', r'\1, getUsuarioLocal \2', content)

    # Add ShieldAlert to lucide-react if not present
    if "ShieldAlert" not in content:
        content = re.sub(r'(import \{[^}]*)\}( from "lucide-react";?)', r'\1, ShieldAlert \2', content)

    # Add const [souAdmin, setSouAdmin] = useState(true);
    # after the component definition. Look for export default function
    func_pattern = r'(export default function [a-zA-Z0-9_]+\([^)]*\) \{)'
    content = re.sub(func_pattern, r'\1\n  const [souAdmin, setSouAdmin] = useState(true);', content)

    # Add useEffect modification
    # Find existing useEffect(() => {
    # If no useEffect is there at all, we might need to add it, but all pages probably have one.
    if "useEffect(() => {" in content:
        content = re.sub(
            r'(useEffect\(\(\) => \{)', 
            r'\1\n    const local = getUsuarioLocal();\n    setSouAdmin(local?.papel === "admin");',
            content,
            count=1
        )
    else:
        # If there's no useEffect at all (rare, but maybe in some pages), let's insert one.
        # This regex looks for setSouAdmin and adds it below
        content = re.sub(
            r'(const \[souAdmin, setSouAdmin\] = useState\(true\);)',
            r'\1\n  useEffect(() => {\n    const local = getUsuarioLocal();\n    setSouAdmin(local?.papel === "admin");\n  }, []);',
            content
        )

    # Add the return block before `return (`
    return_block = """  if (!souAdmin) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-zinc-400 gap-3">
        <ShieldAlert className="h-10 w-10" />
        <p className="text-sm">Esta área é restrita a administradores.</p>
      </div>
    );
  }

  return ("""
    # Find the last `return (` that is for the component rendering.
    # Usually it's `  return (`
    content = re.sub(r'(\s+)return \($', r'\1' + return_block.replace('\n', '\n\\1')[:-3] + 'return (', content, flags=re.MULTILINE)
    
    # Actually wait, replacing `return (` with regex multiline can be tricky.
    # Let's do it safer by finding the outermost `return (` or finding the `return (` that is preceded by 2 spaces.
    content = content.replace("  return (", "  if (!souAdmin) {\n    return (\n      <div className=\"flex flex-col items-center justify-center py-20 text-zinc-400 gap-3\">\n        <ShieldAlert className=\"h-10 w-10\" />\n        <p className=\"text-sm\">Esta área é restrita a administradores.</p>\n      </div>\n    );\n  }\n\n  return (")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Patched {file_path}")
