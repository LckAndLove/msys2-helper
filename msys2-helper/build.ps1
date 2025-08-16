param(
	[string]$Name = "C++ Runtime Installer(VSCode,Cursor,Trae,Kiro)"
)

Write-Host "Building with PyInstaller, output name: $Name"

# Export the name via environment variable to avoid command-line encoding issues.
$env:PYINSTALLER_OUTPUT_NAME = $Name

# Quick test mode: set environment variable PYINSTALLER_TEST=1 to only verify name passing.
if ($env:PYINSTALLER_TEST -eq '1') {
	Write-Host "Test mode: PYINSTALLER_OUTPUT_NAME = $env:PYINSTALLER_OUTPUT_NAME"
	exit 0
}

# Prepare a temporary Python script (UTF-8) that calls PyInstaller programmatically.
$py = @'
import os
from PyInstaller.__main__ import run

name = os.environ.get('PYINSTALLER_OUTPUT_NAME') or 'install_msys2'
args = [
	'--onefile',
	'--windowed',
	'--icon', 'msys2.ico',
	'--add-data', 'msys2.ico;.',
	'--hidden-import', 'collections.abc',
	'--hidden-import', 'traceback',
	'--name', name,
	'install_msys2.py'
]
print('PyInstaller args:', args)
run(args)
'@

$tmp = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), [System.IO.Path]::GetRandomFileName() + '.py')
[System.IO.File]::WriteAllText($tmp, $py, [System.Text.Encoding]::UTF8)
Write-Host "Running Python with temporary script $tmp"
& python $tmp
Remove-Item $tmp -ErrorAction SilentlyContinue