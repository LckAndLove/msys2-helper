if (Test-Path __pycache__) { Remove-Item -Recurse -Force __pycache__ }
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }

Remove-Item -Recurse -Force .\install_msys2.spec