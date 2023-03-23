import logging
import argparse
import pytest

logger = logging.getLogger()


def is_application_installed(cli_obj, app_name):
    app_installed = False
    app_package_repo_dict = cli_obj.app_ext.parse_app_package_list_dict()
    if app_name in app_package_repo_dict:
        app_info = app_package_repo_dict[app_name]
        if app_info["Status"] == 'Installed':
            app_installed = True

    return app_installed


def test_remove_app_extension(cli_objects, remove_app_extension):
    cli_obj = cli_objects.dut
    apps_list = remove_app_extension
    not_installed_apps = []
    if not apps_list:
        pytest.skip("No App Extensions selected, Please specify a valid argument on --remove_app_extension")
    for app_name in apps_list:
        logger.info("Checking if {} is installed on DUT".format(app_name))
        if not is_application_installed(cli_obj, app_name):
            logger.error("{} isn't installed on DUT".format(app_name))
            not_installed_apps.append(app_name)
            continue
        cli_obj.app_ext.remove_selected_app_extension(app_name)
    if not_installed_apps:
        if len(not_installed_apps) == len(apps_list):
            raise AssertionError("Error in removing {}, these App Extensions aren't installed on the DUT"
                                 .format(not_installed_apps))
        raise Exception("The following app extensions weren't removed: {}, please check logs"
                        .format(not_installed_apps))
