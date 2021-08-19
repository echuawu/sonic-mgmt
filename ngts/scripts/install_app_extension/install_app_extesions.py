#!/usr/bin/env python
import pytest
import logging
import allure
import json
from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli
from ngts.constants.constants import AppExtensionInstallationConstants
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
    dut_engine = topology_obj.players['dut']['engine']
    if SonicAppExtensionCli.verify_version_support_app_ext(dut_engine):
        app_ext_installer = AppExtensionInstaller(dut_engine, app_extension_dict_path)
        app_ext_installer.install_supported_app_extensions()
    else:
        pytest.skip('The image does not support app extension')


class AppExtensionInstaller():
    def __init__(self, dut_engine, app_extension_dict_path):
        self.dut_engine = dut_engine
        if app_extension_dict_path:
            self.app_extension_dict = self._json_load_app_extension_info(app_extension_dict_path)
        else:
            self.app_extension_dict = self.get_latest_applications()
        self.is_app_extension_present_in_application_list()
        self.syncd_sdk_version = self.get_sdk_version(AppExtensionInstallationConstants.SYNCD_DOCKER)

    def get_latest_applications(self):
        # TODO add implementation for latest applications fetch
        pytest.skip('Skipping. Fetching latest implementation of app extension is not yet implemented.')

    @staticmethod
    def _json_load_app_extension_info(app_extension_dict_path):
        try:
            with open(app_extension_dict_path, 'r') as f:
                return json.load(f)
        except json.decoder.JSONDecodeError as e:
            logger.error('Please check the content of provided json file: {}'.format(app_extension_dict_path))
            raise e

    def is_app_extension_present_in_application_list(self):
        for app_ext in self.app_extension_dict:
            if app_ext not in AppExtensionInstallationConstants.APPLICATION_LIST:
                raise AppExtensionError(
                    'App extension name "{}" is not defined in APPLICATION_LIST {}. Please check '
                    ' provided json file'.format(app_ext, AppExtensionInstallationConstants.APPLICATION_LIST))

    def get_supported_app_ext_objects(self):
        application_obj_list = []
        for app in AppExtensionInstallationConstants.APPLICATION_LIST:
            if app in self.app_extension_dict:
                application_obj_list.append(AppExtensionInfo(app, self.app_extension_dict[app]))
        return application_obj_list

    def install_supported_app_extensions(self):
        log_build_supports_app_ext = 'Build supports app extension'
        with allure.step(log_build_supports_app_ext):
            logger.info(log_build_supports_app_ext)
            for app_ext_obj in self.get_supported_app_ext_objects():
                self.install_application(app_ext_obj)

    def install_application(self, app_ext_obj):
        self.remove_app_extension(app_ext_obj)
        self.add_app_ext_repo(app_ext_obj)
        self.install_app_ext(app_ext_obj)
        self.enable_app_ext(app_ext_obj)
        self.check_app_extension_status(app_ext_obj)
        app_ext_obj.set_sdk_version(self.get_sdk_version(app_ext_obj.app_name))
        if not self.is_sdk_version_app_extension_matches_sonic(app_ext_obj):
            raise AppExtensionError('App ext {} sdk {} does not match sonic sdk {}'.format(
                app_ext_obj.app_name, app_ext_obj.sdk_version,
                self.syncd_sdk_version))

    def add_app_ext_repo(self, app_ext_obj):
        log_add_app_ext_repo = 'Adding app extension repository {} on the dut'.format(app_ext_obj.repository)
        with allure.step(log_add_app_ext_repo):
            logger.info(log_add_app_ext_repo)
            SonicAppExtensionCli.add_repository(self.dut_engine, app_ext_obj.app_name, app_ext_obj.repository)

    def install_app_ext(self, app_ext_obj):
        log_install_app_ext_version = 'Installing app extension {} version {} on the dut'.\
            format(app_ext_obj.app_name, app_ext_obj.version)
        with allure.step(log_install_app_ext_version):
            logger.info(log_install_app_ext_version)
            SonicAppExtensionCli.install_app(
                self.dut_engine, app_name=app_ext_obj.app_name,
                from_repository='{}:{}'.format(app_ext_obj.repository, app_ext_obj.version))

    def enable_app_ext(self, app_ext_obj):
        log_enable_ext_app = 'Enabling app extension {} on the dut'.format(app_ext_obj.app_name)
        with allure.step(log_enable_ext_app):
            logger.info(log_enable_ext_app)
            SonicAppExtensionCli.enable_app(self.dut_engine, app_ext_obj.app_name)

    def disable_app_ext(self, app_ext_obj):
        log_enable_ext_app = 'Disabling app extension {} on the dut'.format(app_ext_obj.app_name)
        with allure.step(log_enable_ext_app):
            logger.info(log_enable_ext_app)
            SonicAppExtensionCli.enable_app(self.dut_engine, app_ext_obj.app_name)

    def check_app_extension_status(self, app_ext_obj):
        log_check_app_ext = 'Checking app extension {} on the dut'.format(app_ext_obj.app_name)
        with allure.step(log_check_app_ext):
            logger.info(log_check_app_ext)
            if 'lastrc' in app_ext_obj.version:
                retry_verify_app_container_up(self.dut_engine, app_ext_obj.app_name)
            else:
                verify_app_container_up_and_repo_status_installed(self.dut_engine, app_ext_obj.app_name,
                                                                  app_ext_obj.version)

    def is_sdk_version_app_extension_matches_sonic(self, app_ext_obj):
        log_check_app_ext_sdk = 'Checking syncd sdk version {} matches app extension {} sdk version on the dut'.\
            format(self.syncd_sdk_version, app_ext_obj.app_name)
        with allure.step(log_check_app_ext_sdk):
            logger.info(log_check_app_ext_sdk)
            return self.syncd_sdk_version == app_ext_obj.sdk_version

    def get_sdk_version(self, docker_name):
        return self.dut_engine.run_cmd(AppExtensionInstallationConstants.CMD_GET_SDK_VERSION.format(docker_name),
                                       validate=True)

    def remove_app_extension(self, app_ext_obj):
        log_is_app_ext_installed = 'Checking if {} app ext already installed'.format(app_ext_obj.app_name)
        with allure.step(log_is_app_ext_installed):
            logger.info(log_is_app_ext_installed)
            if app_ext_obj.app_name in SonicAppExtensionCli.show_app_list(self.dut_engine):
                self.uninstall_app_ext(app_ext_obj)
                self.remove_repository_app_ext(app_ext_obj)

    def uninstall_app_ext(self, app_ext_obj):
        log_uninstall_app_ext = 'Uninstalling app extension {} on the dut'.format(app_ext_obj.app_name)
        with allure.step(log_uninstall_app_ext):
            logger.info(log_uninstall_app_ext)
            self.disable_app_ext(app_ext_obj)
            SonicAppExtensionCli.uninstall_app(self.dut_engine, app_ext_obj.app_name)

    def remove_repository_app_ext(self, app_ext_obj):
        log_remove_repository_app_ext = 'Remove repository app extension {} on the dut'.format(app_ext_obj.app_name)
        with allure.step(log_remove_repository_app_ext):
            logger.info(log_remove_repository_app_ext)
            SonicAppExtensionCli.remove_repository(self.dut_engine, app_ext_obj.app_name)


class AppExtensionError(Exception):
    pass
