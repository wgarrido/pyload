# -*- coding: utf-8 -*-

import urlparse

from module.plugins.internal.Hoster import Hoster
from module.utils import save_path as safe_filename


class Crypter(Hoster):
    __name__    = "Crypter"
    __type__    = "crypter"
    __version__ = "0.05"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),  #: Overrides core.config.get("general", "folder_per_package")
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Base decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    html = None  #: Last html loaded  #@TODO: Move to Hoster


    def __init__(self, pyfile):
        super(Crypter, self).__init__(pyfile)

        #: Put all packages here. It's a list of tuples like: ( name, [list of links], folder )
        self.packages = []

        #: List of urls, pyLoad will generate packagenames
        self.urls = []


    def process(self, pyfile):
        """
        Main method
        """
        self.decrypt(pyfile)

        if self.urls:
            self._generate_packages()

        elif not self.packages:
            self.error(_("No link grabbed"), "decrypt")

        self._create_packages()


    def decrypt(self, pyfile):
        raise NotImplementedError


    def _generate_packages(self):
        """
        Generate new packages from self.urls
        """
        packages = [(name, links, None) for name, links in self.core.api.generatePackages(self.urls).iteritems()]
        self.packages.extend(packages)


    def _create_packages(self):
        """
        Create new packages from self.packages
        """
        package_folder   = self.pyfile.package().folder
        package_password = self.pyfile.package().password
        package_queue    = self.pyfile.package().queue

        folder_per_package    = self.core.config.get("general", "folder_per_package")
        use_subfolder         = self.get_config('use_subfolder', folder_per_package)
        subfolder_per_package = self.get_config('subfolder_per_package', True)

        for name, links, folder in self.packages:
            self.log_debug("Parsed package: %s" % name,
                          "%d links" % len(links),
                          "Saved to folder: %s" % folder if folder else "Saved to download folder")

            pid = self.core.api.addPackage(name, self.fixurl(links), package_queue)

            if package_password:
                self.core.api.setPackageData(pid, {"password": package_password})

            #: Workaround to do not break API addPackage method
            setFolder = lambda x: self.core.api.setPackageData(pid, {"folder": x or ""})

            if use_subfolder:
                if not subfolder_per_package:
                    setFolder(package_folder)
                    self.log_debug("Set package %(name)s folder to: %(folder)s" % {"name": name, "folder": folder})

                elif not folder_per_package or name != folder:
                    if not folder:
                        folder = urlparse.urlparse(name).path.split("/")[-1]

                    setFolder(safe_filename(folder))
                    self.log_debug("Set package %(name)s folder to: %(folder)s" % {"name": name, "folder": folder})

            elif folder_per_package:
                setFolder(None)