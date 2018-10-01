import pkg_resources
import collections

def info():
    LauncherInfo = collections.namedtuple('LauncherInfo', ['icon_text', 'program_name', 'icon_filename'])
    return LauncherInfo('script', 'msgscript', pkg_resources.resource_filename('msgtools', 'script/script.png'))
