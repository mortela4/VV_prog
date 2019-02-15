import gooey
gooey_root = os.path.dirname(gooey.__file__)
gooey_languages = Tree(os.path.join(gooey_root, 'languages'), prefix = 'gooey/languages')
gooey_images = Tree(os.path.join(gooey_root, 'images'), prefix = 'gooey/images')
a = Analysis(['fwproggui.py', 'fwprog.py'],
             pathex=['E:\\kode\\py_proj\\VV_prog'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None,
             )
pyz = PYZ(a.pure)

options = [('u', None, 'OPTION')]

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          options,
          gooey_languages,
          gooey_images,
          name='fwprog_gui',
          debug=False,
          strip=None,
          upx=True,
          console=True,
          windowed=True,
          icon=os.path.join(gooey_root, 'images', 'program_icon.ico'))

