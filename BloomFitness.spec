# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file para BloomFitness.

Para generar el ejecutable:
    pyinstaller BloomFitness.spec
"""

import os
from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(SPECPATH)

# Análisis de dependencias
a = Analysis(
    ['main.py'],
    pathex=[str(BASE_DIR)],
    binaries=[],
    datas=[
        # Incluir estilos QSS
        (str(BASE_DIR / 'src' / 'ui' / 'styles'), 'src/ui/styles'),
        # Incluir assets
        (str(BASE_DIR / 'assets'), 'assets'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'sqlalchemy.dialects.sqlite',
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

# Crear archivo PYZ con módulos Python compilados
pyz = PYZ(a.pure, a.zipped_data)

# Crear ejecutable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BloomFitness',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Agregar icono aquí si se tiene: icon='assets/icon.ico'
)
