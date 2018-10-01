import pkg_resources
import collections

def info():
    LauncherInfo = collections.namedtuple('LauncherInfo', ['icon_text', 'program_name', 'icon_filename'])
    return LauncherInfo('inspector', 'msginspector', pkg_resources.resource_filename('msgtools', 'inspector/inspector.png'))
