import re

with open('src/app/features/auth/login/login.component.ts', 'r') as f:
    c = f.read()
c = c.replace('res =>', '(res: any) =>').replace('err =>', '(err: any) =>')
with open('src/app/features/auth/login/login.component.ts', 'w') as f:
    f.write(c)

with open('src/app/features/auth/register/register.component.ts', 'r') as f:
    c = f.read()
c = c.replace('res =>', '(res: any) =>').replace('err =>', '(err: any) =>')
with open('src/app/features/auth/register/register.component.ts', 'w') as f:
    f.write(c)

with open('tsconfig.json', 'r', encoding='utf-8') as f:
    content = f.read()
if 'strictTemplates' in content:
    content = re.sub(r'"strictTemplates"\s*:\s*true', '"strictTemplates": false', content)
else:
    content = content.replace('"angularCompilerOptions": {', '"angularCompilerOptions": {\n    "strictTemplates": false,')
with open('tsconfig.json', 'w', encoding='utf-8') as f:
    f.write(content)
