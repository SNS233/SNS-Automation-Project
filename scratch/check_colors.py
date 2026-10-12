import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'style=' in line:
        for s in re.findall(r'style="([^"]*)"', line):
            if any(k in s.lower() for k in ['#fff', '#ffffff', '#0f172a', '#1e293b', '#f8fafc', '#e2e8f0', '#334155', '#475569', '#64748b']):
                print(f'{i+1}: {s}')
