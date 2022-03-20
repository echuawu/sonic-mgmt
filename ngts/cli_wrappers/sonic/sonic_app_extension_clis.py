import logging

from ngts.cli_util.cli_parsers import generic_sonic_output_parser
from infra.tools.connection_tools.linux_ssh_engine import LinuxSshEngine


logger = logging.getLogger()


class SonicAppExtensionCli:
    """
    This class hosts SONiC APP Extension cli methods
    """

    def __init__(self):
        pass

    @staticmethod
    def add_repository(engine, app_name, repository_name, version=None):
        if version:
            engine.run_cmd('sudo sonic-package-manager repository add {} {} --default-reference={}'.format(app_name, repository_name, version), validate=True)
        else:
            engine.run_cmd('sudo sonic-package-manager repository add {} {}'.format(app_name, repository_name), validate=True)

    @staticmethod
    def remove_repository(engine, app_name):
        engine.run_cmd('sudo sonic-package-manager repository remove {}'.format(app_name), validate=True)

    @staticmethod
    def install_app(engine, app_name, version="", from_repository=''):
        if version:
            engine.run_cmd('sudo sonic-package-manager install {}=={} -y'.format(app_name, version), validate=True)
        elif from_repository:
            engine.run_cmd('sudo sonic-package-manager install --from-repository {} -y'.format(from_repository), validate=True)
        else:
            engine.run_cmd('sudo sonic-package-manager install {} -y'.format(app_name), validate=True)

    @staticmethod
    def uninstall_app(engine, app_name, is_force=True):
        if is_force:
            engine.run_cmd('sudo sonic-package-manager uninstall {} -y --force'.format(app_name), validate=True)
        else:
            engine.run_cmd('sudo sonic-package-manager uninstall {} -y'.format(app_name), validate=True)

    @staticmethod
    def show_app_list(engine):
        return engine.run_cmd('sudo sonic-package-manager list')

    @staticmethod
    def parse_app_package_list_dict(engine):
        """
        Parse app package data into dict by "sonic-package-manager list" output
        :param engine: ssh engine object
        :Return app package dict, or raise exception
        """
        app_package_repo_list = SonicAppExtensionCli.show_app_list(engine)
        app_package_repo_dict = generic_sonic_output_parser(app_package_repo_list,
                                                            headers_ofset=0,
                                                            len_ofset=1,
                                                            data_ofset_from_start=2,
                                                            data_ofset_from_end=None,
                                                            column_ofset=2,
                                                            output_key='Name')
        return app_package_repo_dict

    @staticmethod
    def uninstall_app(engine, app_name, is_force=False):
        if is_force:
            engine.run_cmd('sudo sonic-package-manager uninstall --force {} -y'.format(app_name), validate=True)
        else:
            engine.run_cmd('sudo sonic-package-manager uninstall {} -y'.format(app_name), validate=True)

    @staticmethod
    def enable_app(engine, app_name):
        engine.run_cmd('sudo config feature state {} enabled'.format(app_name), validate=True)

    @staticmethod
    def disable_app(engine, app_name):
        engine.run_cmd('sudo config feature state {} disabled'.format(app_name), validate=True)

    @staticmethod
    def install_app_from_tarball(engine, tarball_name):
        engine.run_cmd("sudo spm install -y --from-tarball {}".format(tarball_name), validate=True)

    @staticmethod
    def upgrade_app(engine, app_name: str, version: str, is_force_upgrade: bool = False, validate: bool = True,
                    allow_downgrade: bool = False) -> str:
        """
        Upgrade app with specified version from repo:
        :param engine: ssh engine object
        :param app_name: app name
        :param version:  app package version
        :param allow_downgrade: allow downgrade, True is allow downgrade, False is not allow
        Return output from command
        """
        allow_downgrade_option = "--allow-downgrade" if allow_downgrade else ""
        if is_force_upgrade:
            output = engine.run_cmd("sudo sudo spm install -y -f {}={} {}".format(app_name, version,
                                                                                  allow_downgrade_option),
                                    validate=validate)
        else:
            output = engine.run_cmd("sudo sudo spm install -y {}={} {}".format(app_name, version,
                                                                               allow_downgrade_option),
                                    validate=validate)

        return output

    @staticmethod
    def upgrade_app_from_tarbll(engine, tarball_name: str) -> None:
        """
        Upgrade app with specified version from tarball:
        :param engine: ssh engine object
        :param tarball_name: app name
        :parm validate: bool
        """
        engine.run_cmd("sudo spm upgrade -y --from-tarball {}".format(tarball_name))

    @staticmethod
    def show_app_version(engine: LinuxSshEngine, app_name: str, option: str = "") -> str:
        """
        Show app version:
        :param engine: ssh engine object
        :param app_name: app name
        :param option: "", plain, all
        :Return app version info
        """
        if option:
            option = "--{}".format(option)
        return engine.run_cmd("sudo spm show package versions {} {}".format(app_name, option), validate=True)

    @staticmethod
    def show_app_manifest(engine: LinuxSshEngine, app_name: str, version: str = "") -> str:
        """
        Show app manifest:
        :param engine: ssh engine object
        :param app_name: app name
        :param version: app version
        :Return specified version app manifest
        """
        return engine.run_cmd("sudo spm show package manifest {}={} ".format(app_name, version), validate=True)

    @staticmethod
    def show_app_changelog(engine: LinuxSshEngine, app_name: str, version: str = "") -> str:
        """
        Show app version:
        :param engine: ssh engine object
        :param app_name: app name
        :param version: app version
        :Return specified version app changelog
        """
        return engine.run_cmd("sudo spm show package changelog {}={} ".format(app_name, version), validate=True)

    @staticmethod
    def verify_version_support_app_ext(dut_engine):
        """
        Verify if the version support app ext feature by finding the cmd of sonic-package-manager or not
        :param dut_engine: ssh engine object
        :return True if support app ext, else False
        """
        app_ext_cmd_prefix = 'sonic-package-manager'
        output = dut_engine.run_cmd('which {}'.format(app_ext_cmd_prefix))
        if app_ext_cmd_prefix in output:
            return True
        return False

    @staticmethod
    def get_installed_app_version(engine_dut, app_name):
        """
        get the installed app version
        :param engine_dut: ssh engine object
        :param app_name: app name
        :return: the installed app version
        """
        apps_dict = SonicAppExtensionCli.parse_app_package_list_dict(engine_dut)
        app_dict = apps_dict[app_name]
        return app_dict['Version']
