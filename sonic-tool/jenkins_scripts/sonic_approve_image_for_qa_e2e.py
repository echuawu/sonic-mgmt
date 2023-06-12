"""
This script used by Jenkins job: http://jenkins-fit81-sws.mellanox.com/job/sonic_approve_image_for_qa_e2e/
This script creates HTML - which will be send in email at the end of Jenkins job execution
Script doing next:
 - Get environment variables
 - Create HTML with next content:
    - Email header
    - Info about PRs and issues - if available
 - Write HTML file
"""

import os

# Gen env variables
included_prs = os.environ.get('INCLUDED_PRS')
not_included_prs = os.environ.get('NOT_INCLUDED_PRS')
fixed_issues = os.environ.get('FIXED_ISSUES')
known_issues = os.environ.get('KNOWN_ISSUES')


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


def create_email(included_prs=None, not_included_prs=None, fixed_issues=None, known_issues=None):
    email_body = ''

    email_header = '<p style="font-size:14px">Hi All,</p>' \
                   '<p style="font-size:14px">This version is approved for QA and E2E.</p>'

    email_body += email_header

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

    create_email(included_prs, not_included_prs, fixed_issues, known_issues)
