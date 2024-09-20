import os
import sys
import platform

block_cipher = None

# Determine platform and architecture
current_platform = platform.system().lower()
architecture = 'x64' if sys.maxsize > 2**32 else 'x86'

chrome_portable_path = './chrome_portable'
chromedriver_path = './chromedriver'

# Set the executable name based on the platform
if current_platform.startswith('win'):
    exe_name = f'spaces_tool_windows_{architecture}'
elif current_platform == 'darwin':
    exe_name = f'spaces_tool_macos_{architecture}'
else:
    exe_name = 'spaces_tool_linux'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (chrome_portable_path, 'chrome_portable'),
        (chromedriver_path, 'chromedriver')
    ],
    hiddenimports=['tkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
