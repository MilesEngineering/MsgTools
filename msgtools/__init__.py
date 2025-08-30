def check_version():
    import json
    import os
    from packaging import version
    import importlib.metadata
    try:
        msgtools_distribution = importlib.metadata.distribution("msgtools")
        version_filename = ".msgtools_requirement.json"
        searchdir = os.getcwd()
        while(True):
            required_version_file = os.path.join(searchdir, version_filename)
            if os.path.isfile(required_version_file):
                with open(required_version_file, 'r') as version_file:
                    j = json.load(version_file)
                    required_version = version.parse(j["version"])
                    if version.Version(msgtools_distribution.version) < required_version:
                        # Bit of an ugly hack, but try to determine if the msgtools package was installed
                        # editable, to give a better hint to the user of how to upgrade it.
                        installed_editable = "egg-info" in str(msgtools_distribution.files)

                        print("ERROR!")
                        print("msgtools version %s < required version %s" % (msgtools_distribution.version, required_version))
                        print("Required version is set by the contents of:\n    %s" % (required_version_file))
                        print("To resolve this, you should update msgtools, perhaps with:")
                        if installed_editable:
                            install_dir = importlib.util.find_spec('msgtools').origin.replace("__init__.py", "")
                            print("    cd %s" % (install_dir))
                            print("    git pull")
                        else:
                            print("    pip3 install --user --break-system-packages --upgrade msgtools ")
                        exit(1)

            lastsearchdir = searchdir
            searchdir = os.path.abspath(os.path.join(searchdir, os.pardir))
            # checking if joining with pardir returns the same dir is the easiest way to
            # determine if we're at root of filesystem, and our upward search has to stop.
            if lastsearchdir == searchdir:
                break
    except importlib.metadata.PackageNotFoundError:
        # If msgtools is not installed, but we are somehow running anyway,
        # then don't do version checks.
        pass

check_version()

# Create shortcuts for importing the most common items from msgtools
from .lib.app import App
from .lib.gui import Gui
from .lib.message import Message
from .lib.messaging import Messaging
Messages = Messaging.Messages
