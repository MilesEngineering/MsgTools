import importlib
import collections

def info():
    LauncherInfo = collections.namedtuple('LauncherInfo', ['icon_text', 'program_name', 'icon_filename'])
    return LauncherInfo('script', 'msgscript', importlib.resources.files('msgtools') / 'script/script.png')
