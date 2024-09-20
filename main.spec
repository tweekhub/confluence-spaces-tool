import os
import sys

block_cipher = None

# Determine platform and architecture
platform = sys.platform
architecture = 'x64' if '64' in os.uname().machine else 'x86'

chrome_portable_path = './chrome_portable'
chromedriver_path = './chromedriver'

# Set the executable name based on the platform
if platform.startswith('win'):
    exe_name = 'spaces_tool_windows'
elif platform == 'darwin':
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
