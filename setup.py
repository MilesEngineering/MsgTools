from setuptools import setup, find_packages

setup(name='msgtools',
    version='0.28.31',
    description='Tools for fixed binary protocols',
    url='https://github.com/MilesEngineering/MsgTools/',
    author='Miles Gazic',
    author_email='miles.gazic@gmail.com',
    license='GPLv2',
    packages=find_packages(),
    zip_safe=False,
    entry_points = {
        'console_scripts': ['msgparser=msgtools.parser.parser:main',
                            'msgcheck=msgtools.parser.check:main',
                            'msgconsole=msgtools.console.console:main',
                            'msginflux=msgtools.database.influxdb:main'],
        'gui_scripts': ['msgscope=msgtools.scope.scope:main [gui]',
                        'msgserver=msgtools.server.server:main [gui]',
                        'msginspector=msgtools.inspector.inspector:main [gui]',
                        'msgmultilog=msgtools.multilog.multilog:main [gui]',
                        'msggoodlistener=msgtools.goodlistener.goodlistener:main [gui]',
                        'msgplot=msgtools.lib.msgplot:main [gui]',
                        'msgbandwidthtestecho=msgtools.noisemaker.bandwidthtestecho:main [gui]',
                        'msgbandwidthtester=msgtools.noisemaker.bandwidthtester:main [gui]',
                        'msgnoisemaker=msgtools.noisemaker.noisemaker:main [gui]',
                        'msglumberjack=msgtools.lumberjack.lumberjack:main [gui]'],
        'msgtools.parser.plugin': ['c=msgtools.parser.c.language',
                                   'cpp=msgtools.parser.cpp.language',
                                   'java=msgtools.parser.java.language',
                                   'javascript=msgtools.parser.javascript.language',
                                   'python=msgtools.parser.python.language',
                                   'html=msgtools.parser.html.language',
                                   'matlab=msgtools.parser.matlab.language',
                                   'swift=msgtools.parser.swift.language'],
        'msgtools.server.plugin': ['serial=msgserver.serial:serial']
    },
    install_requires=[
        'pyyaml',
        'websockets',
        'janus'
    ],
    extras_require={
        'gui':  ["pyqt5", "pyqtgraph"],
        'serverserial': ["pyqtserial"],
    },
    package_data={
        # Include all Template files for the code generator
        '': ['*Template*', 'bootstrap.min.css']
    }
)
