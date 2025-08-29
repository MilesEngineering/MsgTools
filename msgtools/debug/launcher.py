import importlib
import collections

def info():
    LauncherInfo = collections.namedtuple('LauncherInfo', ['icon_text', 'program_name', 'icon_filename'])
    return LauncherInfo('debug', 'msgdebug', importlib.resources.files('msgtools') / 'debug/debug.png')
