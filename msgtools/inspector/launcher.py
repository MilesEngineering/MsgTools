import importlib
import collections

def info():
    LauncherInfo = collections.namedtuple('LauncherInfo', ['icon_text', 'program_name', 'icon_filename'])
    return LauncherInfo('inspector', 'msginspector', importlib.resources.files('msgtools') / 'inspector/inspector.png')
