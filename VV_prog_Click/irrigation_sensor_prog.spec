# -*- mode: python ; coding: utf-8 -*-

# NOTE: 'pyinstaller' must be run from within Anaconda shell if Anaconda Python installation is used!

block_cipher = None


a = Analysis(['irrigation_sensor_prog.py'],
             pathex=['P:\\MortenL\\proj_info\\VannVogn\\firm_ware\\VV_flash_prog_proj\\VV_prog\\VV_prog_Click'],
             binaries=[('JLink.exe', '.'), ('JLinkARM.dll', '.')],
             datas=[('copy.png', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='irrigation_sensor_prog',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
