import importlib
import collections

def info():
    LauncherInfo = collections.namedtuple('LauncherInfo', ['icon_text', 'program_name', 'icon_filename'])
    return LauncherInfo('noisemaker', 'msgnoisemaker', importlib.resources.files('msgtools') / 'noisemaker/noisemaker.png')
