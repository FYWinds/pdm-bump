from argparse import ArgumentParser, Namespace
from typing import Optional, cast
from pdm.cli.commands.base import BaseCommand
from pdm import termui
from pdm.core import Project
from pep440_version_utils import Version
from .config import Config

class BumpCommand(BaseCommand):
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument('what', action='store', choices=['major', 'minor', 'micro', 'pre-release', 'no-pre-release'], default=None, help="The part of the version to bump according to PEP 440: major.minor.micro.")
        parser.add_argument('--pre', action='store', choices=['alpha', 'beta', 'rc', 'c'], default=None, help="Sets a pre-release on the current version. If a pre-release is set, it can be removed using the final option. A new pre-release must greater then the current version. See PEP440 for details.")
        parser.add_argument("--dry-run", action='store_false', help='Do not perform a log-in')
        parser.description = "Bumps the version to a next version according to PEP440."

    def handle(self, project: Project, options: Namespace) -> None:
        log = project.core.ui.echo
        config: Config = Config(project.pyproject)
        version_value: Optional[str] = cast(Optional[str], config.get_pyproject_value("project", "version"))

        if version_value is None:
            log (termui.red("Cannot find version in {}".format(termui.bold(project.pyproject_file))))
            return

        version: Version = Version(version_value)
        next_version: Optional[Version] = None
        if options.what is not None:
            if "major" == options.what:
                next_version = version.next_major()
            elif "minor" == options.what:
                next_version = version.next_minor()
            elif "micro" == options.what:
                next_version = version.next_micro()
            elif "pre-release" == options.what:
                if options.pre is not None:
                    if "alpha" == options.pre:
                        next_version = version.next_alpha()
                    elif "beta" == options.pre:
                        next_version = version.next_beta()
                    elif options.pre in ["rc", "c"]:
                        next_version = version.next_release_candidate()
                    else:
                        log(termui.red("Invalid pre-release: {}. Must be one of alpha, beta, rc or c".format(options.pre)))
                        return
                else:
                    log(termui.red("No pre-release kind set. Please provide one of the following values: alpha, beta, rc, c"))
                    return
            elif "no-pre-release" == options.what:
                next_version = Version("{major}.{minor}.{micro}".format(
                    major=version.major,
                    minor=version.minor,
                    micro=version.micro
                ))
            else:
                log(termui.red("Invalid version part to bump: {}. Must be one of major, minor, micro, pre-release or no-prerelease.".format(options.what)))
                return
        
        else:
            log(termui.red("No version part to bump set. Please provide on of the following values: major, minor, micro, pre-release or no-prerelease"))
            return

        if next_version is not None:
            config.set_pyproject_value(str(next_version), "project, version")
            project.write_pyproject(True)
        else:
            log(termui.red("Failed to update version: No version set in pyproject.toml"))
            return

