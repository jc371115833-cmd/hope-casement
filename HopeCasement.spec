# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter

ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ['src\\hopecasement\\__init__.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src\\assets\\images\\*', 'assets\\images'),
        (os.path.join(ctk_path, 'assets'), 'customtkinter\\assets'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'customtkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HopeCasement',
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
    icon='setup\\window_writingascreenwindo_ventana_deescritura_10765.ico',
)
