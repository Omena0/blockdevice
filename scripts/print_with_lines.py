from pathlib import Path
p = Path('d:/GitHub/ui-engine-v2/main.py')
text = p.read_text()
for i, l in enumerate(text.splitlines(), start=1):
    print(f"{i:03}: {l}")
