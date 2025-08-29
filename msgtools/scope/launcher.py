import importlib
import collections

def info():
    LauncherInfo = collections.namedtuple('LauncherInfo', ['icon_text', 'program_name', 'icon_filename'])
    return LauncherInfo('scope', 'msgscope', importlib.resources.files('msgtools') / 'scope/scope.png')
