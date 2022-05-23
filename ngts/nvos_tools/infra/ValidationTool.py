import logging
from .ResultObj import ResultObj, IssueType
import allure

logger = logging.getLogger()


class ValidationTool:

    @staticmethod
    def verify_expected_output(show_cmd_output, str_to_search_for, should_be_found=True):
        """
        Searching for specified str in provided output
        :param show_cmd_output: output of the show commands
        :param str_to_search_for: str to search for
        :param should_be_found: True if str_to_search_for should be found in the output. False - otherwise
        :return: ResultObj
        """
        with allure.step('Verify `{str}` {can} be found in provided output str'.format(str=str_to_search_for,
                                                                                       can="can" if should_be_found else "can't")):
            result_obj = ResultObj(result=True, info="", issue_type=IssueType.PossibleBug)
            if not show_cmd_output or not str_to_search_for:
                result_obj.result = False
                result_obj.info = "Invalid input"
                return result_obj

            if str_to_search_for in show_cmd_output:
                if should_be_found:
                    result_obj.info = "{str_to_search_for} was found".format(str_to_search_for=str_to_search_for)
                else:
                    result_obj.result = False
                    result_obj.info = "{str_to_search_for} was found while it should not".format(str_to_search_for=str_to_search_for)
            else:
                if should_be_found:
                    result_obj.result = False
                    result_obj.info = "{str_to_search_for} was not found".format(str_to_search_for=str_to_search_for)
                else:
                    result_obj.info = "{str_to_search_for} was not found as expected".format(str_to_search_for=str_to_search_for)
            return result_obj

    @staticmethod
    def verify_field_exist_in_json_output(json_output, keys_to_search_for, should_be_found=True):
        """
        Searching for specified str in provided json output
        :param json_output: json dictionary
        :param keys_to_search_for: list of keys to search for
        :param should_be_found: True if key_str_to_search_for should be found in the output. False - otherwise
        :return: ResultObj
        """
        with allure.step('Verify field `{field}` {exist} in json output'.format(field=keys_to_search_for,
                                                                                exist="exists" if should_be_found else "doesn't exist")):
            result_obj = ResultObj(result=True, info="", issue_type=IssueType.PossibleBug)
            if not json_output or not keys_to_search_for or len(keys_to_search_for) == 0:
                result_obj.result = False
                result_obj.info = "Invalid input"
                return result_obj

            for key in keys_to_search_for:
                if key in json_output.keys():
                    if should_be_found:
                        logging.info("'{str_to_search_for}' field was found".format(str_to_search_for=key))
                    else:
                        result_obj.result = False
                        result_obj.info = "'{str_to_search_for}' field was found while it should not".format(
                            str_to_search_for=key)
                        break
                else:
                    if should_be_found:
                        result_obj.result = False
                        result_obj.info = "'{str_to_search_for}' field was not found".format(str_to_search_for=key)
                        break
                    else:
                        logging.info("'{str_to_search_for}' field was not found as expected".format(str_to_search_for=key))

            return result_obj

    @staticmethod
    def verify_field_value_in_output(output_dictionary, field_name, expected_value, should_be_equal=True):
        """
        Verify that the value of the field is equal to expected
        :param output_dictionary: output_dictionary
        :param field_name: field name to check its' value
        :param expected_value: expected value of the field
        :param should_be_equal: True if the value of field_name should be equal to expected_value. False - otherwise
        :return:
        """
        with allure.step('Verify the value of {field} is {no}equal to {expected} as expected'.format(
                         field=field_name, expected=expected_value, no="" if should_be_equal else "not ")):
            result_obj = ResultObj(result=True, info="", issue_type=IssueType.PossibleBug)
            if field_name not in output_dictionary.keys():
                result_obj.result = False
                result_obj.info = "Field {field_name} can't be found".format(field_name=field_name)

            if output_dictionary[field_name].strip() == expected_value.strip():
                if should_be_equal:
                    logging.info("The value of {field_name} is '{expected_value}' as expected".format(
                        field_name=field_name, expected_value=expected_value))
                else:
                    result_obj.result = False
                    result_obj.info = "The value of {field_name} is equal to '{expected_value}' while it " \
                                      "should not".format(field_name=field_name, expected_value=expected_value)
            else:
                if should_be_equal:
                    result_obj.result = False
                    result_obj.info = "The value of {field_name} is not '{expected_value}'".format(
                        field_name=field_name, expected_value=expected_value)
                else:
                    logging.info("The value of {field_name} is not '{expected_value}' as expected".format(
                        field_name=field_name, expected_value=expected_value))
            return result_obj

    @staticmethod
    def compare_values(value1, value2):
        """
        Compares two values
        :param value1: first value
        :param value2: second value
        :return: ResultObj - while ResultObj.returned_value = True if the values are equal, False - otherwise
        """
        result_obj = None
        if not value1:
            result_obj = ResultObj(False, "First value is not valid")
        if not value2:
            result_obj = ResultObj(False, "Second value is not valid")
        elif value1 == value2:
            result_obj = ResultObj(True, "The values are equal", True)
        return result_obj

    @staticmethod
    def verify_all_fileds_value_exist_in_output_dictionary(output_dictionary):
        with allure.step('Verify all the fields values are not None'):
            result_obj = ResultObj(result=True, info="", issue_type=IssueType.PossibleBug)
            for key, value in output_dictionary.items():
                if not value:
                    result_obj.result = False
                    result_obj.info += "The value of {field_name} not as expected".format(
                        field_name=key)
            return result_obj
