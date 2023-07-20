if 1:
    import json
    import os
    from packaging import version
    import pkg_resources
    try:
        msgtools_distribution = pkg_resources.get_distribution("msgtools")
        install_dir = msgtools_distribution.egg_info
        msgtools_version = version.parse(msgtools_distribution.version)

        version_filename = ".msgtools_requirement.json"
        searchdir = os.getcwd()
        while(True):
            required_version_file = os.path.join(searchdir, version_filename)
            if os.path.isfile(required_version_file):
                with open(required_version_file, 'r') as version_file:
                    j = json.load(version_file)
                    required_version = version.parse(j["version"])
                    if msgtools_version < required_version:
                        print("ERROR!")
                        print("msgtools version %s < required version %s" % (msgtools_version, required_version))
                        print("Required version is set by the contents of:\n    %s" % (required_version_file))
                        print("To resolve this, you should update msgtools, perhaps with:")
                        if install_dir.endswith(".egg-info"):
                            print("    cd %s" % (install_dir.replace("msgtools.egg-info", "")))
                            print("    git pull")
                            print("    make undevelop ; make develop")
                        else:
                            print("    pip3 install --upgrade msgtools")
                        exit(1)

            lastsearchdir = searchdir
            searchdir = os.path.abspath(os.path.join(searchdir, os.pardir))
            # checking if joining with pardir returns the same dir is the easiest way to
            # determine if we're at root of filesystem, and our upward search has to stop.
            if lastsearchdir == searchdir:
                break
    except pkg_resources.DistributionNotFound:
        # If msgtools is not installed, but we are somehow running anyway,
        # then don't do version checks.
        pass
