# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 (OmniSenseVoice)
用法:
    pyinstaller build.spec
产出: dist/OmniSenseVoice/OmniSenseVoice.exe (OneDir 模式)
"""

from PyInstaller.utils.hooks import collect_all, collect_data_files

# 收集带原生库的依赖
datas = []
binaries = []
hiddenimports = []

for pkg in ['sherpa_onnx', 'sounddevice', 'soundfile', 'numpy', 'pynput', 'pyperclip']:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# Windows 上 pynput 的 win32 后端
hiddenimports += [
    'pynput.keyboard._win32',
    'pynput.mouse._win32',
]

# GUI 支持
hiddenimports += [
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'tkinter.scrolledtext',
]

# 收集我们的 UI 模块
datas += [('ui', 'ui')]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OmniSenseVoice',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='OmniSenseVoice',
)
