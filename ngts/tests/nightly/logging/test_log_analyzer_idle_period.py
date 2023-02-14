import re
import allure
import logging

logger = logging.getLogger()

END_MARKER_PREFIX = 'end-LogAnalyzer'
PATTERN = re.compile(r'/var/log/syslog.(\d+)', re.IGNORECASE)


def test_check_errors_in_log_during_last_idle_period(engines, request, loganalyzer):
    """
    Test checks errors in logs which happen during last idle period
    This test should be executed as pre test case.
    Test logic is next:
    - Get syslog file with last end string
    - Get current LogAnalyzer start_string as variable and remove existing start_string from syslog file
    - Update LogAnalyzer start_string and put it instead of last end_string
    - Then on teardown step LogAnalyzer will analyze all logs since start_string till end_string(which will be
            added after current test case automatically by LogAnalyzer logic)
    Note: The test doesn't make sense to run after install image from ONIE,
            test should be run only after other tests which used LA
    :param engines: engines fixture
    :param request: pytest build-in
    """
    end_string_line, last_end_marker_file = get_last_end_string(engines.dut)

    if end_string_line:
        start_string_line = get_la_start_string(engines.dut, request)
        replace_start_marker(engines.dut, start_string_line, end_string_line, last_end_marker_file)
    else:
        logger.warning('No end-LogAnalyzer marker found. It is a first test')

    # Logic below is required to overcome the issue the when end_marker is not present in syslog - in this case,
    # the end_marker will be added forcefully
    logger.info('Adding end_marker in syslog. Command below may fail, but we do not care about it -'
                ' LA will do the same after test executed(it will pass)')
    for dut in loganalyzer:
        run_id = loganalyzer[dut].ansible_loganalyzer.run_id
        engines.dut.run_cmd(f'sudo python /tmp/loganalyzer.py --action add_end_marker --run_id {run_id}')


def get_la_start_string(engine, request):
    """
    Get LogAnalyzer start string line and remove line which was added by LogAnalyzer at the beginning of current test
    :param engine: dut engine object
    :param request: pytest build-in
    :return: LogAnalyzer start_string line
        example: Jan 19 08:08:48.543280 r-bulldog-02 INFO start-LogAnalyzer-test_max_limit[core].2023-01-19-05:59:30
    """
    test_name = request.node.name
    start = 'start-LogAnalyzer'
    start_prefix = start + '-' + test_name

    msg = 'Getting original LogAnalyzer start_string'
    with allure.step(msg):
        logger.info(msg)
        start_string_full_line = engine.run_cmd(f'sudo cat /var/log/syslog -n | grep {start_prefix}')
        # line example:  "   9	Jan 19 08:08:48.543280 r-bulldog-02 INFO
        #  start-LogAnalyzer-test_max_limit[core].2023-01-19-05:59:30"
        start_string_line = start_string_full_line.split('\t')[1]
        start_string_line_number = start_string_full_line.split()[0]

    msg = 'Remove original LogAnalyzer start_string'
    with allure.step(msg):
        logger.info(msg)
        engine.run_cmd(f'sudo sed -i \'{start_string_line_number}d\' /var/log/syslog')

    return start_string_line


def get_last_end_string(engine):
    """
    Get LogAnalyzer last end string line
    :param engine: dut engine object
    :return: LogAnalyzer end_string line
            example: Jan 19 08:08:48.543280 r-bulldog-02 INFO end-LogAnalyzer-test_max_limit[core].2023-01-19-05:59:30
    """
    msg = 'Getting latest end-LogAnalyzer string'
    with allure.step(msg):
        logger.info(msg)
        # this case is separate to save the time in cmd to get all syslog files
        # as in almost all cases the last file will contain the end string
        end_string_full_line = find_last_end_marker_in_file(engine, '/var/log/syslog')
        if end_string_full_line:
            end_string_file = '/var/log/syslog'
        else:
            end_string_full_line, end_string_file = search_in_all_syslog_files(engine)

    return end_string_full_line, end_string_file


def search_in_all_syslog_files(engine):
    """
    Searching the last end string line in all syslog files.
    :param engine: dut engine object
    :return: LogAnalyzer end_string line
            example: Jan 19 08:08:48.543280 r-bulldog-02 INFO end-LogAnalyzer-test_max_limit[core].2023-01-19-05:59:30
    """
    end_string_full_line = ''
    end_string_file = ''
    syslog_files_list = engine.run_cmd(f'sudo ls /var/log/syslog.*').split()
    syslog_files_list.sort(key=extract_number_from_syslog_name)
    for file_path in syslog_files_list:
        end_string_full_line = find_last_end_marker_in_file(engine, file_path)
        if END_MARKER_PREFIX in end_string_full_line:
            end_string_file = file_path
            break
    return end_string_full_line, end_string_file


def extract_number_from_syslog_name(s):
    return int(PATTERN.search(s).group(1))


def find_last_end_marker_in_file(engine, file_path):
    """
    Look to specific file if the end string is contained
    :param engine: dut engine object
    :param file_path: path to syslog file
    :return: LogAnalyzer end_string line
            example: Jan 19 08:08:48.543280 r-bulldog-02 INFO end-LogAnalyzer-test_max_limit[core].2023-01-19-05:59:30
    """
    search_tool = 'grep'
    if '.gz' in file_path:
        search_tool = 'zgrep'
    string_full_line = engine.run_cmd(f'sudo {search_tool} {END_MARKER_PREFIX} {file_path} | tail -1')
    return string_full_line


def replace_start_marker(engine, new_start_line, end_string_line, last_end_marker_file):
    """
    Replace new LogAnalyzer start string instead of last end string
    :param engine: due engine
    :param new_start_line: new LogAnalyzer start string
    :param end_string_line: original LogAnalyzer end string
    :param last_end_marker_file: syslog file with end_string_line
    """
    logger.info(f"The new start marker: {new_start_line}")
    logger.info(f"The latest end marker: {end_string_line}")
    end_string_regex = update_end_string_to_regex(end_string_line)
    logger.info(f"The latest end marker regex: {end_string_regex}")

    if '.gz' in last_end_marker_file:
        not_gz_last_end_marker_file = last_end_marker_file.replace('.gz', '')
        engine.run_cmd(f"sudo gzip -dk {last_end_marker_file}", validate=True)
        engine.run_cmd(f"sudo sed -i 's/{end_string_regex}/{new_start_line}/g'"
                       f" {not_gz_last_end_marker_file}", validate=True)
        engine.run_cmd(f"sudo gzip -f {not_gz_last_end_marker_file}", validate=True)
    else:
        engine.run_cmd(f"sudo sed -i 's/{end_string_regex}/{new_start_line}/g' {last_end_marker_file}", validate=True)


def update_end_string_to_regex(end_string_line):
    """
    Replace end string to regex "start with", as the string can contain the special characters in the name of test
    :param end_string_line: original LogAnalyzer end string
    :return: LogAnalyzer end regex,
            example:
             Before: Jan 19 08:08:48.543280 r-bulldog-02 INFO end-LogAnalyzer-test_max_limit[core].2023-01-19-05:59:30
             After:  ^Jan 19 08:08:48.543280 r-bulldog-02 INFO end-LogAnalyzer.*
    """
    prefix = end_string_line.split(END_MARKER_PREFIX)[0]
    end_string_regex = f'^{prefix}{END_MARKER_PREFIX}.*'
    return end_string_regex
