# ResilientEdge Packaging Script
Write-Host "Creating ResilientEdge_COMPLETE_FINAL.zip..." -ForegroundColor Cyan

$zipName = "ResilientEdge_COMPLETE_FINAL.zip"
if (Test-Path $zipName) {
    Remove-Item $zipName -Force
}

# Use python zip script for cross-platform reliability
python -c "
import zipfile, os

exclude_dirs = {'.git', 'node_modules', '.venv', '__pycache__', '.pytest_cache', 'dist', 'build'}
exclude_files = {'ResilientEdge_COMPLETE_FINAL.zip'}

with zipfile.ZipFile('ResilientEdge_COMPLETE_FINAL.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            if f in exclude_files or f.endswith('.pyc') or f.endswith('.tmp'):
                continue
            filepath = os.path.join(root, f)
            arcname = os.path.relpath(filepath, '.')
            zf.write(filepath, arcname)

print('Packaged ResilientEdge_COMPLETE_FINAL.zip successfully.')
"
