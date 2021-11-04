
def verify_deviation(value, expected_value, deviation):
    """
    Check the value in expected range - expected value with deviation.
    :param value: topology_obj fixture
    :param expected_value: expected value
    :param deviation: allowed deviation from 0 to 1
    :return: raise assertion error in case the value not as expected with deviation
    """
    assert int(value) > int(expected_value) * (1 - deviation), \
        "The value {} is less then expected {} with deviation of {}%".format(value, expected_value, deviation)
    assert int(value) < int(expected_value) * (1 + deviation), \
        "The value {} is bigger then expected {} with deviation of {}".format(value, expected_value, deviation)
