# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the Protein Purification backend server.
# Run: pyinstaller server.spec
#
# Output: dist/protein-purification-server/  (one directory, used by Electron)

a = Analysis(
    ["server.py"],
    pathex=["."],
    binaries=[],
    datas=[
        # Non-Python assets that must travel with the bundle
        ("data/mixtures", "data/mixtures"),
        ("frontend/dist", "frontend/dist"),
    ],
    hiddenimports=[
        # uvicorn dynamically imports these via importlib
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "PIL",
        "IPython",
        "pytest",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="protein-purification-server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="protein-purification-server",
)
