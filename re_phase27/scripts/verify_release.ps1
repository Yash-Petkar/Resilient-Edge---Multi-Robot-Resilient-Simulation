$ErrorActionPreference = "Stop"
Write-Host "ResilientEdge release verification" -ForegroundColor Cyan
python -m compileall -q backend core experiments
if ($LASTEXITCODE -ne 0) { throw "Python compile check failed" }
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Python test suite failed" }
python -c "from pathlib import Path; import re; root=Path('src'); missing=[]; files=list(root.rglob('*.ts'))+list(root.rglob('*.tsx')); [missing.append((str(f),m.group(1))) for f in files for m in re.finditer(r'(?:from|import)\s*[''\"](\.[^''\"]+)[''\"]', f.read_text(errors='ignore')) if not any(c.exists() for c in [(f.parent/m.group(1)),Path(str(f.parent/m.group(1))+'.ts'),Path(str(f.parent/m.group(1))+'.tsx'),Path(str(f.parent/m.group(1))+'.js'),Path(str(f.parent/m.group(1))+'.jsx'),f.parent/m.group(1)/'index.ts',f.parent/m.group(1)/'index.tsx'])]; print('Frontend relative-import audit:', 'PASS' if not missing else missing); raise SystemExit(0 if not missing else 1)"
if ($LASTEXITCODE -ne 0) { throw "Frontend relative-import audit failed" }
npm run lint
if ($LASTEXITCODE -ne 0) { throw "Frontend TypeScript lint failed" }
npm run build
if ($LASTEXITCODE -ne 0) { throw "Frontend production build failed" }
Write-Host "RELEASE VERIFICATION PASSED" -ForegroundColor Green
