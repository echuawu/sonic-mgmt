#!/usr/bin/env python
import pytest
import logging
import allure
import json

from ngts.constants.constants import AppExtensionInstallationConstants, P4SamplingConsts
from ngts.tests.nightly.app_extension.app_extension_helper import verify_app_container_up_and_repo_status_installed, \
    retry_verify_app_container_up
from ngts.scripts.install_app_extension.app_extension_info import AppExtensionInfo


logger = logging.getLogger()


def test_install_all_supported_app_extensions(topology_obj, app_extension_dict_path):
    """
    This function will perform installation of app extensions
    :param topology_obj: topology object fixture
    :param app_extension_dict_path: path to app extension dict
    """
    cli_obj = topology_obj.players['dut']['cli']
    skip_reason = install_all_supported_app_extensions(cli_obj, app_extension_dict_path)
    if skip_reason:
        pytest.skip(skip_reason)


def install_all_supported_app_extensions(cli_obj, app_extension_dict_path):
    """
    This function will perform installation of app extensions
    :param cli_obj: dut cli_obj object
    :param app_extension_dict_path: path to app extension dict
    :return: return the skip reason if the test need to be skipped, else return None
    """
    skip_reason = ""
    if not app_extension_dict_path:
        logger.info("app_extension_dict_path is not provided, skip the installing the app extensions")
        skip_reason = 'app_extension_dict_path is not provided'
    elif cli_obj.app_ext.verify_version_support_app_ext():
        app_ext_installer = AppExtensionInstaller(cli_obj, app_extension_dict_path)
        app_ext_installer.install_supported_app_extensions()
        cli_obj.general.save_configuration()
    else:
        logger.info("The image does not support app extension")
        skip_reason = 'The image does not support app extension'
    return skip_reason


class AppExtensionInstaller:
    def __init__(self, cli_obj, app_extension_dict_path):
        self.cli_obj = cli_obj
        self.app_extension_dict = self.set_app_extension_dict(app_extension_dict_path)
        self.is_app_extension_present_in_application_list()
        self.syncd_sdk_version = self.get_sdk_version(AppExtensionInstallationConstants.SYNCD_DOCKER)

    def get_latest_applications(self):
        # TODO add implementation for latest applications fetch
        pytest.skip('Skipping. Fetching latest implementation of app extension is not yet implemented.')

    def set_app_extension_dict(self, app_extension_dict_path):
        try:
            with open(app_extension_dict_path, 'r') as f:
                app_extension_dict = json.load(f)
                return self.map_project_to_application_name(app_extension_dict)
        except json.decoder.JSONDecodeError as e:
            logger.error(f'Please check the content of provided json file: {app_extension_dict_path}')
            raise e

    def is_app_extension_present_in_application_list(self):
        for app_ext in self.app_extension_dict:
            if app_ext not in AppExtensionInstallationConstants.APPLICATION_LIST:
                raise AppExtensionError(
                    f'App extension name "{app_ext}" is not defined in APPLICATION_LIST '
                    f'{AppExtensionInstallationConstants.APPLICATION_LIST}. Please check provided json file')

    def map_project_to_application_name(self, app_extension_dict):
        for app_ext_project, app_name in AppExtensionInstallationConstants.APP_EXTENSION_PROJECT_MAPPING.items():
            if app_ext_project in app_extension_dict:
                self.replace_project_name_to_application_name(app_extension_dict, app_ext_project, app_name)
        return app_extension_dict

    @staticmethod
    def replace_project_name_to_application_name(app_extension_dict, app_ext_project, app_name):
        repository_url = app_extension_dict[app_ext_project]
        del app_extension_dict[app_ext_project]
        app_extension_dict[app_name] = repository_url

    def get_supported_app_ext_objects(self):
        application_obj_list = []
        for app in AppExtensionInstallationConstants.APPLICATION_LIST:
            if app in self.app_extension_dict:
                application_obj_list.append(AppExtensionInfo(app, self.app_extension_dict[app]))
        return application_obj_list

    def install_supported_app_extensions(self):
        log_build_supports_app_ext = 'Build supports app extension'

        self.cli_obj.bgp.shutdown_bgp_all()
        try:
            with allure.step(log_build_supports_app_ext):
                logger.info(log_build_supports_app_ext)
                for app_ext_obj in self.get_supported_app_ext_objects():
                    app_installed, requested_version = self.is_application_installed(app_ext_obj)
                    if app_installed:
                        if requested_version:
                            logger.info(
                                f'Skipping installation for {app_ext_obj.app_name} since it is already installed')
                            continue
                        else:
                            logger.info(f"App {app_ext_obj.app_name} is installed with different "
                                        f"version than the requested one")
                            with allure.step(f"Uninstalling {app_ext_obj.app_name}, the version is not as requested"):
                                self.uninstall_application(app_ext_obj)
                    self.install_application(app_ext_obj)
        except Exception as err:
            raise err
        finally:
            self.cli_obj.bgp.startup_bgp_all()

    def uninstall_application(self, app_ext_obj):
        log_uninstall_app_ext_version = f'Uninstalling app extension {app_ext_obj.app_name}'
        with allure.step(log_uninstall_app_ext_version):
            self.cli_obj.app_ext.disable_app(app_ext_obj.app_name)
            self.cli_obj.app_ext.uninstall_app(app_name=app_ext_obj.app_name)
            self.cli_obj.app_ext.remove_repository(app_ext_obj.app_name)

    def install_application(self, app_ext_obj):
        log_install_app_ext_version = f'Installing app extension {app_ext_obj.app_name}'
        with allure.step(log_install_app_ext_version):
            self.add_app_ext_repo(app_ext_obj)
            self.install_app_ext(app_ext_obj)
            self.enable_app_ext(app_ext_obj)
            self.check_app_extension_status(app_ext_obj)
            self.check_app_ext_sdk_version(app_ext_obj)

    def is_application_installed(self, app_ext_obj):
        app_installed = False
        requested_version = False
        app_package_repo_dict = self.cli_obj.app_ext.parse_app_package_list_dict()
        if app_ext_obj.app_name in app_package_repo_dict:
            app_info = app_package_repo_dict[app_ext_obj.app_name]
            if app_info["Status"] == 'Installed':
                app_installed = True
            if app_info["Version"] == app_ext_obj.version:
                requested_version = True
        return app_installed, requested_version

    def check_app_ext_sdk_version(self, app_ext_obj):
        if not app_ext_obj.is_sx_sdk_version_present():
            logger.warning(f'Skipping checking of sdk_version for {P4SamplingConsts.APP_NAME}')
            return
        app_ext_obj.set_sdk_version(self.get_sdk_version(app_ext_obj.app_name))
        if not self.is_sdk_version_app_extension_matches_sonic(app_ext_obj):
            raise AppExtensionError(f'App ext {app_ext_obj.app_name} sdk {app_ext_obj.sdk_version} '
                                    f'does not match sonic sdk {self.syncd_sdk_version}')

    def add_app_ext_repo(self, app_ext_obj):
        log_add_app_ext_repo = f'Adding app extension repository {app_ext_obj.repository} on the dut'
        with allure.step(log_add_app_ext_repo):
            logger.info(log_add_app_ext_repo)
            self.cli_obj.app_ext.add_repository(app_ext_obj.app_name, app_ext_obj.repository)

    def install_app_ext(self, app_ext_obj):
        log_install_app_ext_version = f'Installing app extension {app_ext_obj.app_name} ' \
                                      f'version {app_ext_obj.version} on the dut'
        with allure.step(log_install_app_ext_version):
            logger.info(log_install_app_ext_version)
            self.cli_obj.app_ext.install_app(
                app_name=app_ext_obj.app_name,
                from_repository=f'{app_ext_obj.repository}:{app_ext_obj.version}')

    def enable_app_ext(self, app_ext_obj):
        log_enable_ext_app = f'Enabling app extension {app_ext_obj.app_name} on the dut'
        with allure.step(log_enable_ext_app):
            logger.info(log_enable_ext_app)
            self.cli_obj.app_ext.enable_app(app_ext_obj.app_name)

    def disable_app_ext(self, app_ext_obj):
        log_disable_ext_app = f'Disabling app extension {app_ext_obj.app_name} on the dut'
        with allure.step(log_disable_ext_app):
            logger.info(log_disable_ext_app)
            self.cli_obj.app_ext.disable_app(app_ext_obj.app_name)

    def check_app_extension_status(self, app_ext_obj):
        log_check_app_ext = f'Checking app extension {app_ext_obj.app_name} on the dut'
        with allure.step(log_check_app_ext):
            logger.info(log_check_app_ext)
            if 'lastrc' in app_ext_obj.version:
                retry_verify_app_container_up(self.cli_obj, app_ext_obj.app_name)
            else:
                verify_app_container_up_and_repo_status_installed(self.cli_obj, app_ext_obj.app_name,
                                                                  app_ext_obj.version)

    def is_sdk_version_app_extension_matches_sonic(self, app_ext_obj):
        log_check_app_ext_sdk = f'Checking syncd sdk version {self.syncd_sdk_version} matches app extension ' \
                                f'{app_ext_obj.app_name} sdk version on the dut'
        with allure.step(log_check_app_ext_sdk):
            logger.info(log_check_app_ext_sdk)
            return self.syncd_sdk_version == app_ext_obj.sdk_version

    def get_sdk_version(self, docker_name):
        return self.cli_obj.general.engine.run_cmd(
            AppExtensionInstallationConstants.CMD_GET_SDK_VERSION.format(docker_name), validate=True)


class AppExtensionError(Exception):
    pass
