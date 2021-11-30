"""
This script used by Jenkins job: http://jenkins-fit81-sws.mellanox.com/job/sonic_approve_image_for_qa_e2e/
This script creates HTML - which will be send in email at the end of Jenkins job execution
Script doing next:
 - Get environment variables
 - Get info about applications WJH/LCM
 - Create HTML with next content:
    - Email header
    - Info about apps(WJH/LCM) - if available
    - Info about PRs and issues - if available
 - Write HTML file
"""

import os
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
build_id = os.environ['BUILD_ID']

wjh_ver = os.environ.get('WJH_VER')
lcm_ver = os.environ.get('LCM_VER')
wjh_included_in_image = False
lcm_included_in_image = False

included_prs = os.environ.get('INCLUDED_PRS')
not_included_prs = os.environ.get('NOT_INCLUDED_PRS')
fixed_issues = os.environ.get('FIXED_ISSUES')
known_issues = os.environ.get('KNOWN_ISSUES')


def get_apps_info_from_build_params(wjh_ver, wjh_included_in_image, lcm_ver, lcm_included_in_image):
    """
    Get info about WJH/LCM from build parameters
    :param wjh_ver: wjh version
    :param wjh_included_in_image: True/False
    :param lcm_ver: lcm version
    :param lcm_included_in_image: True/False
    :return: wjh_ver, wjh_included_in_image, lcm_ver, lcm_included_in_image
    """
    print('Getting WJH/LCM versions info from orignal build job "sonic_build" build id {}'.format(build_id))
    api_url = 'http://jenkins-fit81-sws.mellanox.com/job/sonic_build/{}/api/json'.format(build_id)
    response = {}
    if requests_imported:
        response = requests.get(api_url).json()
    else:
        if urllib_imported:
            response = json.loads(urllib.urlopen(api_url).read().decode('utf-8'))

    for action in response['actions']:
        if action.get('parameters'):
            build_params = action['parameters']
            wjh_ver, wjh_included_in_image = get_application_version_info_from_build_params(build_params,
                                                                                            app_param_name='WJH_VERSION',
                                                                                            app_ver=wjh_ver)
            lcm_ver, lcm_included_in_image = get_application_version_info_from_build_params(build_params,
                                                                                            app_param_name='LCM_VERSION',
                                                                                            app_ver=lcm_ver)

    print('WJH versions is: {}, is included in image: {}'.format(wjh_ver, wjh_included_in_image))
    print('LCM versions is: {}, is included in image: {}'.format(lcm_ver, lcm_included_in_image))

    return wjh_ver, wjh_included_in_image, lcm_ver, lcm_included_in_image


def get_application_version_info_from_build_params(build_params, app_param_name, app_ver, app_included_in_image=False):
    """
    Get info about application from build parameters
    :param build_params: dict with build parameters
    :param app_param_name: name of parameter
    :param app_ver: application version, if not provided and we able to get from build params - will return app ver
    :param app_included_in_image: is app included in image
    :return: app version and True/False about is it included in image
    """
    for parameter in build_params:
        if parameter['name'] == app_param_name:
            if not app_ver:
                app_ver = parameter['value']
            if parameter['value']:
                app_included_in_image = True

            return app_ver, app_included_in_image


def build_app_info_email_body(app, version, is_included):
    """
    Build email body - part related to applications
    :param app: App name
    :param version: App version
    :param is_included: is app included in SONiC image
    :return: string(html) with info about application
    """
    if not version.startswith('http'):
        version = 'urm.nvidia.com/sw-nbu-sws-sonic-docker/{}:{}'.format(app, version)

    app_info = '<tr style="height: 18px;">' \
               '<td style="width: 50%; height: 18px;">{}</td>' \
               '<td style="width: 25%; height: 18px;">{}</td>' \
               '<td style="width: 25%; height: 18px;">{}</td>' \
               '</tr>'.format(app, version, is_included)
    return app_info


def build_email_info_about_apps(wjh_ver, wjh_included_in_image, lcm_ver, lcm_included_in_image):
    """
    Add to email info about apps(WJH/LCM)
    :param wjh_ver: WJH ver
    :param wjh_included_in_image: True/False
    :param lcm_ver: LCM ver
    :param lcm_included_in_image: True/False
    :return string(html)
    """
    email_body = ''
    if wjh_ver or lcm_ver:
        wjh_lcp_header = '<table style="border-collapse: collapse; width: 100%; height: 36px;" border="1">' \
                         '<tbody>' \
                         '<tr style="height: 18px; background-color: #777; color: white; font-weight: bold;">' \
                         '<td style="width: 50%;">Application</td>' \
                         '<td style="width: 25%;">Version</td>' \
                         '<td style="width: 25%;">Included in image</td>' \
                         '</tr>'
        email_body += wjh_lcp_header

        if wjh_ver:
            wjh_info = build_app_info_email_body(app='sonic-wjh', version=wjh_ver, is_included=wjh_included_in_image)
            email_body += wjh_info

        if lcm_ver:
            lcm_info = build_app_info_email_body(app='sonic-lcm', version=lcm_ver, is_included=lcm_included_in_image)
            email_body += lcm_info

        wjh_lcm_end = '</tbody>' \
                      '</table>'
        email_body += wjh_lcm_end
    return email_body


def build_extended_email_body(title, extended_list):
    """
    Build extended part of email body(PRs, issues)
    :param title: title
    :param extended_list: list of issues/prs
    :return: string(html)
    """
    issue_pr_body = ''
    issue_pr_header = '<br>' \
                      '<table style="border-collapse: collapse; width: 100%; height: 36px;" border="1">' \
                      '<tbody>' \
                      '<tr style="height: 18px; background-color: #777; color: white; font-weight: bold;">' \
                      '<td class="td-title-main" style="height: 18px;">{}</td>' \
                      '</tr>'.format(title)
    issue_pr_body += issue_pr_header

    issue_pr_info = '<tr style="height: 18px;">' \
                    '<td style="width: 100%; height: 18px;">{}. {}</a></td>' \
                    '</tr>'

    counter = 1
    for issue_pr in extended_list:
        issue_pr_body += issue_pr_info.format(counter, issue_pr)
        counter += 1

    issue_pr_end = '</tbody>' \
                   '</table>'
    issue_pr_body += issue_pr_end
    return issue_pr_body


def build_included_prs_email_body(prs_list):
    """
    Build email part related to included prs
    :param prs_list: list of prs
    :return: string(html)
    """
    title = 'Included PRs:'
    return build_extended_email_body(title, prs_list)


def build_not_included_prs_email_body(prs_list):
    """
    Build email part related to not included prs
    :param prs_list: list of prs
    :return: string(html)
    """
    title = 'Not included PRs:'
    return build_extended_email_body(title, prs_list)


def build_fixed_issues_email_body(issues_list):
    """
    Build email part related to fixed issues
    :param issues_list: list of issues
    :return: string(html)
    """
    title = 'Fixed issues:'
    return build_extended_email_body(title, issues_list)


def build_known_issues_email_body(issues_list):
    """
    Build email part related to known fixed issues
    :param issues_list: list of issues
    :return: string(html)
    """
    title = 'Known issues:'
    return build_extended_email_body(title, issues_list)


def create_email(wjh_ver, wjh_included_in_image, lcm_ver, lcm_included_in_image, included_prs, not_included_prs,
                 fixed_issues, known_issues):

    email_body = ''

    email_header = '<p style="font-size:14px">Hi All,</p>' \
                   '<p style="font-size:14px">This version is approved for QA and E2E.</p>'

    email_body += email_header

    email_body += build_email_info_about_apps(wjh_ver, wjh_included_in_image, lcm_ver, lcm_included_in_image)

    if included_prs:
        email_body += build_included_prs_email_body(included_prs.splitlines())

    if not_included_prs:
        email_body += build_not_included_prs_email_body(not_included_prs.splitlines())

    if fixed_issues:
        email_body += build_fixed_issues_email_body(fixed_issues.splitlines())

    if known_issues:
        email_body += build_known_issues_email_body(known_issues.splitlines())

    with open('email_report.html', 'w') as report_file:
        report_file.write(email_body)


if __name__ == "__main__":

    wjh_ver, wjh_included_in_image, lcm_ver, lcm_included_in_image = get_apps_info_from_build_params(wjh_ver,
                                                                                                     wjh_included_in_image,
                                                                                                     lcm_ver,
                                                                                                     lcm_included_in_image)

    create_email(wjh_ver, wjh_included_in_image, lcm_ver, lcm_included_in_image,
                 included_prs, not_included_prs, fixed_issues, known_issues)
