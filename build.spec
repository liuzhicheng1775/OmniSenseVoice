# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置（OmniSenseVoice）
用法：
    pyinstaller build.spec
产出：dist/OmniSenseVoice/OmniSenseVoice.exe（OneDir 模式）

为什么用 OneDir 而不是 OneFile：
- OneFile 模式每次启动要把所有文件解压到临时目录，启动慢（sherpa_onnx + numpy 不小）
- OneDir 模式启动快，分发时打成 zip 给用户解压即可
"""

from PyInstaller.utils.hooks import collect_all

# 收集带原生库的依赖（.pyd / .dll / .so）
datas = []
binaries = []
hiddenimports = []

for pkg in ["sherpa_onnx", "sounddevice", "soundfile", "numpy", "pynput", "pyperclip"]:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# Windows 上 pynput 的 win32 后端
hiddenimports += [
    "pynput.keyboard._win32",
    "pynput.mouse._win32",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除一些不必要的模块，减小体积
        "matplotlib",
        "tkinter",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "pandas",
        "scipy",
        "IPython",
        "jupyter",
        "notebook",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OmniSenseVoice",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # sherpa_onnx 的原生库不要 UPX 压缩，避免加载问题
    console=True,        # 保留控制台，用户要看提示
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="assets/icon.ico",  # 如有图标可放 assets/icon.ico
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="OmniSenseVoice",
)
