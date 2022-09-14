
def verify_deviation(value, expected_value, deviation):
    """
    Check whether a value is within an expected range which is derived from the exacted value and  the deviation.
    :param value: topology_obj fixture
    :param expected_value: expected value
    :param deviation: allowed deviation from 0 to 1
    :return: raise assertion error in case the value not as expected with deviation
    """
    verify_down_deviation(value, expected_value, deviation)
    verify_up_deviation(value, expected_value, deviation)


def verify_down_deviation(value, expected_value, deviation):
    """
    Check the value is bigger than the expected value with deviation.
    :param value: topology_obj fixture
    :param expected_value: expected value
    :param deviation: allowed deviation from 0 to 1
    :return: raise assertion error in case the value not as expected with deviation
    """
    assert float(value) > float(expected_value) * (1 - deviation), \
        "The value {} is less than expected {} with deviation of {}%".format(value, expected_value, deviation)


def verify_up_deviation(value, expected_value, deviation):
    """
    Check the value is lower than the expected value with deviation.
    :param value: topology_obj fixture
    :param expected_value: expected value
    :param deviation: allowed deviation from 0 to 1
    :return: raise assertion error in case the value not as expected with deviation
    """
    assert float(value) < float(expected_value) * (1 + deviation), \
        "The value {} is bigger than expected {} with deviation of {}".format(value, expected_value, deviation)


def verify_deviation_for_simx(value, deviation):
    """
    Check the value in expected range - expected value with deviation.
    :param value: actual pps value
    :param deviation: allowed deviation in packets
    :return: raise assertion error in case the value not as expected with deviation
    """
    assert int(value) < deviation,\
        f"Actual pps value {value} is not less than expected pps value 0 + {deviation}"


def is_feature_ready(cli_objects, feature_name, docker_name):
    """
    Check the feature is ready to test.
    Check the feature status and feature container status.
    :param cli_objects: cli_objects fixture
    :param feature_name: the name of the feature
    :param docker_name: docker name of the feature
    """
    feature_installed_status, feature_installed_msg = is_feature_installed(cli_objects, feature_name)
    feature_en_status, feature_en_msg = is_feature_enabled(cli_objects, feature_name, feature_installed_status)
    docker_status, docker_msg = is_docker_exists(cli_objects, docker_name)
    status = feature_installed_status and feature_en_status and docker_status
    msg = ', '.join(filter(None, [feature_installed_msg, feature_en_msg, docker_msg]))
    return status, msg


def is_feature_installed(cli_objects, feature_name):
    status = True
    msg = ''
    features = cli_objects.dut.general.show_and_parse_feature_status()
    if feature_name not in features:
        status = False
        msg = f"{feature_name} feature is not installed."
    return status, msg


def is_feature_enabled(cli_objects, feature_name, feature_installed=None):
    status = False
    msg = f"{feature_name} feature is disabled."
    if feature_installed is None:
        feature_installed, _ = is_feature_installed(cli_objects, feature_name)
    features = cli_objects.dut.general.show_and_parse_feature_status()
    if feature_installed and features[feature_name]['State'] == 'enabled':
        status = True
        msg = ''
    return status, msg


def is_docker_exists(cli_objects, docker_name):
    status = True
    msg = ''
    docker_status = cli_objects.dut.general.get_container_status(docker_name)
    if docker_status is None:
        status = False
        msg = f"{docker_name} docker doesn't exist"
    return status, msg
