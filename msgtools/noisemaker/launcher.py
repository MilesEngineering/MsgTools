import pkg_resources
import collections

def info():
    LauncherInfo = collections.namedtuple('LauncherInfo', ['icon_text', 'program_name', 'icon_filename'])
    return LauncherInfo('noisemaker', 'msgnoisemaker', pkg_resources.resource_filename('msgtools', 'noisemaker/noisemaker.png'))
