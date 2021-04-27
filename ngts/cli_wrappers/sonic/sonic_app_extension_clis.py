import logging

from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon
from ngts.cli_util.cli_parsers import generic_sonic_output_parser


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
    def install_app(engine, app_name, version=""):
        if version:
            engine.run_cmd('sudo sonic-package-manager install {}=={} -y'.format(app_name, version), validate=True)
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
    def upgrade_app(engine, app_name: str, version: str, is_force_upgrade: bool = False, validate: bool = True) -> str:
        """
        Upgrade app with specified version from repo:
        :param engine: ssh engine object
        :param app_name: app name
        :param version:  app package version
        Return output from command
        """
        if is_force_upgrade:
            output = engine.run_cmd("sudo sudo spm upgrade -y -f {}={}".format(app_name, version), validate=validate)
        else:
            output = engine.run_cmd("sudo sudo spm upgrade -y {}={}".format(app_name, version), validate=validate)

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


