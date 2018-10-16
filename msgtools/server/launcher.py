import pkg_resources
import collections

def info():
    LauncherInfo = collections.namedtuple('LauncherInfo', ['icon_text', 'program_name', 'icon_filename'])
    return LauncherInfo('server', 'msgserver', pkg_resources.resource_filename('msgtools', 'server/server.png'))
