import allure
import os
import logging
import pytest
from datetime import datetime
from retry.api import retry_call
from ngts.constants.constants import SonicConst, PytestConst, NvosCliTypes
import tarfile
import re
import smtplib
from email.mime.text import MIMEText

logger = logging.getLogger()
SENDER_MAIL = 'noreply@sanitizer.com'
NVOS_MAIL = 'ncaro-staff@exchange.nvidia.com'
NVIDIA_MAIL_SERVER = 'mail.nvidia.com'


@pytest.fixture(scope='function')
def test_name(request):
    """
    Method for getting the test name parameter for script check_and_store_sanitizer_dump.py,
    the script will check for sanitizer failures and store dump under test name
    :param request: pytest buildin
    :return: the test name, i.e, push_gate
    """
    return request.config.getoption('--test_name')


@pytest.fixture(scope='function')
def send_mail(request):
    """
    Method for getting the send_mail boolean parameter for script check_and_store_sanitizer_dump.py,
    true, to send the report by mail
    :param request: pytest buildin
    :return: True/False, True to send mail.
    """
    value = request.config.getoption('--send_mail')
    return True if value in ['t', 'T', 'True', 'true', 'TRUE'] else False


def check_sanitizer_and_store_dump(dut_engine, dumps_folder, test_name):
    if have_sanitizer_failed(dut_engine):
        logger.warning("SANITIZER FOUND MEMORY LEAKS AFTER REBOOT")
        logger.info(f"sanitizer files were found at {SonicConst.SANITIZER_FOLDER_PATH}")
        sanitizer_dump_path = create_sanitizer_dump(dut_engine, dumps_folder, test_name)
        return sanitizer_dump_path


def have_sanitizer_failed(dut_engine):
    """
    :param dut_engine: ssh engine object
    :return: return True if sanitizer had detected memory leaks
    """
    check_sanitizer_folder_cmd = \
        f"""[ "$(sudo ls -A {SonicConst.SANITIZER_FOLDER_PATH})" ] && echo 'Not Empty' || echo 'Empty'"""
    res = dut_engine.run_cmd(check_sanitizer_folder_cmd)
    return res == 'Not Empty'


def create_sanitizer_dump(dut_engine, dumps_folder, test_name):
    """
    create a dump for all sanitizer files and store it at dumps_folder
    :param dut_engine: ssh engine object
    :param dumps_folder:  dumps folder path
    :return: sanitizer dump file location
    """
    with allure.step('Generating a dump with sanitizer files'):
        now = datetime.now()
        date_time = now.strftime("%m_%d_%Y_%H:%M:%S")
        sanitizer_dump_filename = f"{test_name}_sanitizer_files_{date_time}.tar.gz".replace("::", "_")
        sanitizer_dump_path = f"/tmp/{sanitizer_dump_filename}"
        add_date_to_files_name(dut_engine)
        dut_engine.run_cmd(f"sudo tar -czvf {sanitizer_dump_path} -C {SonicConst.SANITIZER_FOLDER_PATH} .")
        retry_call(check_dump_was_created, fargs=[dut_engine, sanitizer_dump_path], tries=6,
                   delay=5, logger=logger)
        logger.info(f"Dump was created at: {sanitizer_dump_path}")
    with allure.step(f'Copy dump: {sanitizer_dump_path} to log folder {dumps_folder}'):
        dest_file = dumps_folder + '/dump_' + sanitizer_dump_filename
        logger.info('Copy sanitizer dump {} to dump folder {}'.format(sanitizer_dump_filename, dumps_folder))
        dut_engine.copy_file(source_file=sanitizer_dump_path,
                             dest_file=dest_file,
                             file_system='/',
                             direction='get',
                             overwrite_file=True,
                             verify_file=False)
        os.chmod(dest_file, 0o777)
        logger.warning('SANITIZER DUMP LOCATION: {}'.format(dest_file))
    with allure.step(f'Remove files from {SonicConst.SANITIZER_FOLDER_PATH}'):
        dut_engine.run_cmd(f"sudo rm {SonicConst.SANITIZER_FOLDER_PATH}/*")
    return dest_file


def check_dump_was_created(dut_engine, sanitizer_dump_filename):
    find_res = dut_engine.run_cmd(f"find {sanitizer_dump_filename}")
    assert find_res == sanitizer_dump_filename, f"file {sanitizer_dump_filename} was not created yet"


def add_date_to_files_name(dut_engine):
    rename_files_cmd = """for f in *; do
    fn=$(basename "$f")
    mv "$fn" "$(date -r "$f" +"%Y-%m-%d_%H-%M-%S")_$fn"
    done"""
    dut_engine.run_cmd_set(["sudo su", "cd /var/log/asan", rename_files_cmd, "exit"])


def check_dump_folder_for_existing_sanitizer_files(dut_engine, dumps_folder):
    cmd = f"ls -A {dumps_folder} | grep 'sanitizer_files'"
    files = os.popen(cmd).read()
    files_list = files.split('\n')
    files_list = [file for file in files_list if file]
    return files_list


def aggregate_asan_and_send_mail(mail_address, sanitizer_dump_path, extract_path, setup_name):
    """
    aggregate the asan files from the sanitizer_dump_path - its a tar file.
    extract it to extract_path
    send mail for each daemon with failures , and a summary mail to mail_address
    :param mail_address: mail address to send the mail to
    :param sanitizer_dump_path: the path of the tar file of the asan files
    :param extract_path: path of a directory to extract the file there
    :param setup_name: the setup name
    """
    extract_path = "{}/{}".format(extract_path, "asan")
    logger.info(f"extract files to {extract_path}")
    asan_files_dict = aggregate_asan_files(sanitizer_dump_path, extract_path)
    try:
        s = smtplib.SMTP(NVIDIA_MAIL_SERVER)
        for daemon in asan_files_dict.keys():
            email_contents = orgenize_email_content('\n\n'.join(asan_files_dict[daemon]),
                                                    "Sanitizer errors on daemon {}, on setup {}".format(daemon, setup_name),
                                                    mail_address)
            logger.info(f"sending mail about daemon {daemon}")
            s.sendmail(SENDER_MAIL, email_contents['To'], email_contents.as_string())

        text = 'Sanitizer found errors on daemons: \n{}\nYou should get mail for each daemon\n' \
               'All the ASAN files are here: {}\nTar file:{}'.format(asan_files_dict.keys(), extract_path, sanitizer_dump_path)
        summary_email_contents = orgenize_email_content(text, "Sanitizer report on setup {}".format(setup_name), mail_address)
        s.sendmail(SENDER_MAIL, summary_email_contents['To'], summary_email_contents.as_string())
    finally:
        s.quit()


def orgenize_email_content(content, subject, mail_address):
    email_contents = MIMEText(content)
    email_contents['Subject'] = subject
    email_contents['To'] = mail_address
    return email_contents


def aggregate_asan_files(sanitizer_dump_path, extract_path):
    '''
    aggregate all the asan files that are related to the same daemon and save it in a dictionary
    :param sanitizer_dump_path: the path of the tar file of the asan files
    :param extract_path: path of a directory to extract the file there
    :return:
        asan_files_dict = {
                    'syncd': 'sanitizer error ....',
                    'portsyncd' : 'sanitizer error ....',
                    }
    '''
    try:
        tar = tarfile.open(sanitizer_dump_path, 'r')
        tar.extractall(extract_path)
        asan_files_dict = {}
        for file in tar:
            # take just the daemon name from the file name ( file:2022-05-29_07-59-20_syncd-asan.log.17 , so daemon name: syncd)
            daemon_name = re.findall(r"([a-z]*)-asan", file.name)
            if daemon_name:
                daemon_name = daemon_name[0]
                file_path = extract_path + file.name.replace('./', '/')
                cmd = f"cat {file_path} "
                lines = f"file: {file_path}"
                lines += os.popen(cmd).read()
                tmp_list = asan_files_dict.get(daemon_name, [])
                tmp_list.append(lines)
                asan_files_dict[daemon_name] = tmp_list
    finally:
        tar.close()
    return asan_files_dict


def get_mail_address(topology_obj):
    '''
    :param topology_obj: topology object of the setup
    :return: the mail address to send the report to.
            if its a NVOS system , send to NVOS_EMAILS
    '''
    mail_address = ''
    if topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Topology Conn.']['CLI_TYPE'] in NvosCliTypes.NvueCliTypes:
        mail_address = NVOS_MAIL
    return mail_address


@pytest.mark.disable_loganalyzer
def test_sanitizer(topology_obj, dumps_folder, test_name, send_mail, setup_name):
    if topology_obj.players['dut']['sanitizer']:
        os.environ[PytestConst.GET_DUMP_AT_TEST_FALIURE] = "False"
        dut_engine = topology_obj.players['dut']['engine']
        with allure.step(f'Check if sanitizer has failed in previous reboots'):
            existing_sanitizer_files = check_dump_folder_for_existing_sanitizer_files(dut_engine, dumps_folder)
        with allure.step(f'Reboot DUT'):
            dut_engine.reload([f'sudo reboot'])
        with allure.step(f'Check sanitizer and store dump'):
            sanitizer_dump_path = check_sanitizer_and_store_dump(dut_engine, dumps_folder, test_name)
        with allure.step(f'Check if sanitizer failed after reboot or found dumps during {test_name}.db run'):
            if existing_sanitizer_files or sanitizer_dump_path:
                if existing_sanitizer_files:
                    logger.warning(f"Previous sanitizer dumps were found at {dumps_folder}")
                    for file in existing_sanitizer_files:
                        logger.warning(f"check: {dumps_folder}/{file}")
                if sanitizer_dump_path:
                    logger.warning(f"Sanitizer had failed when preforming reboot, "
                                   f"sanitizer dump is at {sanitizer_dump_path}")
                if send_mail:
                    mail_address = get_mail_address(topology_obj)
                    with allure.step(f'Sending mail with the sanitizer failures to {mail_address}'):
                        aggregate_asan_and_send_mail(mail_address, sanitizer_dump_path, dumps_folder, setup_name)
                raise AssertionError(f"Sanitizer has failed - please check saved dumps at {dumps_folder}")
    else:
        logger.info("Image doesn't include sanitizer - script is not checking for sanitizer dumps")
