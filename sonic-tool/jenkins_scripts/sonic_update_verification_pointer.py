"""
This script used by Jenkins job: http://jenkins-fit81-sws.mellanox.com/job/sonic_update_verification_pointer/
This script updates applications pointer for verification, for specific mars orch scenario
Logic is next:
 - Get environment variables
 - Try to get info about apps(WJH/LCM)
 - If have env var "additional_apps" - and it's path to .deb file - create symbolic link in apps pointer file to it
 - If have env var "additional_apps" - and it's ont path to .deb file - write app ext info to apps pointer file
 - If not env var "additional_apps" and have info about WJH and it .deb file - create symbolic link in apps pointer file to it
 - If not env var "additional_apps" and have info about WJH and it .deb file - write app ext info to apps pointer file
 - If not env var "additional_apps" and have info about WJH and LCM  - write app ext info to apps pointer file
 - in other cases - write string: "Unable to get app info" to apps pointer file
"""

import os
import sys
import json

# Doing imports dynamically to be able to run code on different Python versions with requests/urllib
requests_imported = False
urllib_imported = False
try:
    import requests
    requests_imported = True
except ImportError:
    import urllib
    urllib_imported = True

# Gen env variables
build_id = os.environ.get('BUILD_ID')
mars_orch_scenario = os.environ['MARS_ORCH_SCENARIO']
additional_apps = os.environ.get('ADDITIONAL_APPS')

wjh_ver = os.environ.get('WJH_VER')
lcm_ver = os.environ.get('LCM_VER')


def get_application_version_info_from_build_params(build_params, app_param_name, app_ver):
    """
    Get info about app from build job params
    :param build_params: dict with build params
    :param app_param_name: app_param_name
    :param app_ver: app ver
    :return: app_ver
    """
    for parameter in build_params:
        if parameter['name'] == app_param_name:
            if not app_ver:
                app_ver = parameter['value']
            return app_ver


def get_apps_info_from_build_params(wjh_ver, lcm_ver):
    """
    Get info about WJH/LCM from build parameters
    :param wjh_ver: wjh version
    :param lcm_ver: lcm version
    :return: wjh_ver, lcm_ver
    """
    response = {}
    try:
        print('Getting WJH/LCM versions info from orignal build job "sonic_build" build id {}'.format(build_id))
        api_url = 'http://jenkins-fit81-sws.mellanox.com/job/sonic_build/{}/api/json'.format(build_id)
        if requests_imported:
            response = requests.get(api_url).json()
        else:
            if urllib_imported:
                response = json.loads(urllib.urlopen(api_url).read().decode('utf-8'))
    except Exception as err:
        print('Unable to get info about jenkins build. Error: {}'.format(err))

    if response:
        for action in response['actions']:
            if action.get('parameters'):
                build_params = action['parameters']
                wjh_ver = get_application_version_info_from_build_params(build_params, app_param_name='WJH_VERSION',
                                                                         app_ver=wjh_ver)
                lcm_ver = get_application_version_info_from_build_params(build_params, app_param_name='LCM_VERSION',
                                                                         app_ver=lcm_ver)

    print('WJH versions is: {}'.format(wjh_ver))
    print('LCM versions is: {}'.format(lcm_ver))

    return wjh_ver, lcm_ver


def update_symbolic_link_for_wjh(wjh_ver, dst):
    """
    Update symbolic link for WJH
    :param wjh_ver: path to WJH
    :param dst: apps pointer which should be updated
    """
    src_path = '/auto/sw_system_release{}'.format(wjh_ver.split('auto/sw_system_release')[1])
    os.symlink(src_path, dst)


def update_apps_verification_pointer(mars_orch_scenario, additional_apps, wjh_ver, lcm_ver):
    """
    Update verification pointer(specifc mars orch scenario) for apps
    :param mars_orch_scenario: name of mars orch scenario(branch)
    :param additional_apps: env variable
    :param wjh_ver: env variable
    :param lcm_ver: env variable
    """
    dst = '/auto/sw_regression/system/SONIC/MARS/conf/deploy_configs/verification_app_pointers/{}_app_verification_pointer'.format(mars_orch_scenario)
    try:
        os.remove(dst)
    except Exception as err:
        print('Can not remove app pointer. Error: {}'.format(err))

    if additional_apps:
        if additional_apps.endswith('.deb'):
            update_symbolic_link_for_wjh(additional_apps, dst)
        else:
            app_info = json.loads(additional_apps)
            with open(dst, 'w') as app_ext_ver_pointer:
                json.dump(app_info, app_ext_ver_pointer)
    else:
        app_info = {}
        if wjh_ver and not lcm_ver:
            if wjh_ver.endswith('.deb'):
                update_symbolic_link_for_wjh(wjh_ver, dst)
                sys.exit()
            else:
                app_info = {"what-just-happened": "urm.nvidia.com/sw-nbu-sws-sonic-docker/sonic-wjh:{}".format(wjh_ver)}

        if wjh_ver and lcm_ver:
            app_info = {"what-just-happened": "urm.nvidia.com/sw-nbu-sws-sonic-docker/sonic-wjh:{}".format(wjh_ver),
                        "line-card-manager": "urm.nvidia.com/sw-nbu-sws-sonic-docker/sonic-lcm:{}".format(lcm_ver)}

        with open(dst, 'w') as app_ext_ver_pointer:
            if app_info:
                json.dump(app_info, app_ext_ver_pointer)
            else:
                app_ext_ver_pointer.write('Unable to get app info')


if __name__ == "__main__":
    wjh_ver, lcm_ver = get_apps_info_from_build_params(wjh_ver, lcm_ver)
    update_apps_verification_pointer(mars_orch_scenario, additional_apps, wjh_ver, lcm_ver)
