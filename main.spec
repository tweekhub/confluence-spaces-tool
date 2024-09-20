import os
import sys
import platform
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Determine platform and architecture
current_platform = platform.system().lower()
architecture = 'x64' if sys.maxsize > 2**32 else 'x86'

# Set the executable name based on the platform and architecture
if current_platform.startswith('win'):
    exe_name = f'spaces_tool_windows_{architecture}'
    chrome_portable_path = './chrome_portable/chrome-win64/'
    chromedriver_path = './chromedriver/chromedriver-win64/'
elif current_platform == 'darwin':
    exe_name = f'spaces_tool_macos_{architecture}'
    chrome_portable_path = './chrome_portable/chrome-mac-x64/'
    chromedriver_path = './chromedriver/chromedriver-mac-x64/'
else:
    exe_name = 'spaces_tool_linux'
    chrome_portable_path = './chrome_portable/chrome-linux64/'
    chromedriver_path = './chromedriver/chromedriver-linux64/'

# If running inside a PyInstaller bundle, adjust the paths accordingly
if getattr(sys, 'frozen', False):
    chrome_portable_path = os.path.join(sys._MEIPASS, 'chrome_portable')
    chromedriver_path = os.path.join(sys._MEIPASS, 'chromedriver')

# Bundle the required binaries and data files
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        (os.path.join(chromedriver_path, 'chromedriver'), 'chromedriver'),
        (os.path.join(chrome_portable_path, 'chrome'), 'chrome')
    ],
    datas=[
        ('confluence-api.json', '.'),
        ('confluence-elements.json', '.'),
        ('configuration.yaml', '.'),
        (chrome_portable_path, 'chrome_portable')
    ],
    hiddenimports=collect_submodules('tkinter'),  # Ensure tkinter is bundled
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
    console=False,  # Set to False to disable console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
