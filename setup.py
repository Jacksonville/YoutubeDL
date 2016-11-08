import sys
from cx_Freeze import setup, Executable
from downloader import __version__

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os", "PySide", "bs4"],
                     "excludes": ["tkinter"],
                     "include_files": "ytd.ico"}

bdist_msi_options = {'add_to_path': False,
                     'initial_target_dir': r'[ProgramFilesFolder]\YouTube Downloader'}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"


setup(name="YouTube Downloader",
      version=__version__,
      description="YouTube Downloader",
      options={"build_exe": build_exe_options, 'bdist_msi': bdist_msi_options},
      executables=[Executable("downloader.py",
                              base=base,
                              shortcutName="YouTube Downloader",
                              shortcutDir="ProgramMenuFolder",
                              icon="ytd.ico",
                              targetName="YouTube Downloader.exe")])
