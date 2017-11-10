from setuptools import setup

setup(name='msgtools',
    version='0.1',
    description='Tools for fixed binary protocols',
    url='https://github.com/MilesEngineering/MsgTools/',
    author='Miles Gazic',
    author_email='miles.gazic@gmail.com',
    license='GPLv2',
    packages=['msgtools'],
    zip_safe=False,
    entry_points = {
        'console_scripts': ['msgparser=msgtools.parser.parser:main',
                            'msgcheck=msgtools.check.check:main'],
        'gui_scripts': ['msgscope=msgtools.scope.scope:main [gui]',
                        'msgserver=msgtools.server.server:main [gui]',
                        'msginspector=msgtools.inspector.inspector:main [gui]'],
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
