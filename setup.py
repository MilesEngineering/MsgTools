from setuptools import setup, find_packages

setup(name='msgtools',
    version='0.2',
    description='Tools for fixed binary protocols',
    url='https://github.com/MilesEngineering/MsgTools/',
    author='Miles Gazic',
    author_email='miles.gazic@gmail.com',
    license='GPLv2',
    packages=find_packages(),
    zip_safe=False,
    entry_points = {
        'console_scripts': ['msgparser=msgtools.parser.parser:main',
                            'msgcheck=msgtools.check.check:main',
                            'msgconsole=msgtools.console.console:main'],
        'gui_scripts': ['msgscope=msgtools.scope.scope:main [gui]',
                        'msgserver=msgtools.server.server:main [gui]',
                        'msginspector=msgtools.inspector.inspector:main [gui]',
                        'msgmultilog=msgtools.multilog.multilog:main [gui]',
                        'msggoodlistener=msgtools.goodlistener.goodlistener:main [gui]',
                        'msgplot=msgtools.lib.msgplot:main [gui]',
                        'msgbandwidthtestecho=msgtools.noisemaker.bandwidthtestecho:main [gui]',
                        'msgbadwidthtester=msgtools.noisemaker.bandwidthtester:main [gui]',
                        'msgnoisemaker=msgtools.noisemaker.noisemaker:main [gui]',
                        'msglumberjack=msgtools.lumberjack.lumberjack:main [gui]'],
        'msgtools.parser.plugin': ['c=msgtools.parser.c:c',
                                   'cpp=msgtools.parser.cpp:cpp',
                                   'java=msgtools.parser.java:java',
                                   'javascript=msgtools.parser.java:java',
                                   'python=msgtools.parser.java:java',
                                   'html=msgtools.parser.java:java',
                                   'matlab=msgtools.parser.java:java',
                                   'swift=msgtools.parser.java:java'],
        'msgtools.server.plugin': ['serial=msgserver.serial:serial']
    },
    install_requires={
        'pyyaml'
    },
    extras_require={
        'gui':  ["pyqt5", "pyqtgraph"],
        'serverserial': ["pyqtserial"],
    }
)
