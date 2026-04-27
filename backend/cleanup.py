"""Fix: Remove orphan duplicate HTML builder code from orchestrator.py"""
from pathlib import Path

f = Path(r"c:\Users\Abhinendra Singh\PROJECTS\AI\Gen. AI CheatSheet\backend\src\ai_pipeline\orchestrator.py")
lines = f.read_text(encoding="utf-8").splitlines(keepends=True)

print(f"Original: {len(lines)} lines")

# Find ALL occurrences of "</html>'''" 
html_ends = []
for i, line in enumerate(lines):
    if "</html>'''" in line:
        html_ends.append(i)

print(f"Found </html>''' at lines: {[x+1 for x in html_ends]}")

if len(html_ends) >= 2:
    # First one is end of NEW mind-map builder (keep)
    # Second one is end of OLD duplicate builder (remove)
    first_html_end = html_ends[0]  # end of new code
    
    # Find _build_text_cheatsheet AFTER the second </html>'''
    text_start = None
    for i in range(html_ends[1], len(lines)):
        if "def _build_text_cheatsheet" in lines[i]:
            text_start = i
            break
    
    if text_start:
        print(f"Keeping lines 1-{first_html_end+1}, removing {first_html_end+2}-{text_start}, keeping {text_start+1}-{len(lines)}")
        new_lines = lines[:first_html_end+1] + ["\n"] + lines[text_start:]
        print(f"New: {len(new_lines)} lines (removed {len(lines) - len(new_lines)} lines)")
        f.write_text("".join(new_lines), encoding="utf-8")
        print("✅ Done! Orphan code removed.")
    else:
        print("ERROR: Could not find _build_text_cheatsheet after second </html>'''")
else:
    print("Only one </html>''' found — file may already be clean or structure is different")
    print("Checking for orphan code after first </html>'''...")
    
    first_end = html_ends[0]
    # Check if there's orphan code between first </html>''' and _build_text_cheatsheet
    text_start = None
    for i in range(first_end + 1, len(lines)):
        if "def _build_text_cheatsheet" in lines[i]:
            text_start = i
            break
    
    if text_start and (text_start - first_end) > 5:
        print(f"Found orphan code: lines {first_end+2} to {text_start} ({text_start - first_end - 1} orphan lines)")
        new_lines = lines[:first_end+1] + ["\n"] + lines[text_start:]
        print(f"New: {len(new_lines)} lines")
        f.write_text("".join(new_lines), encoding="utf-8")
        print("✅ Done!")
    else:
        print("File appears clean already.")
