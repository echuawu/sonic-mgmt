import logging
from .ResultObj import ResultObj, IssueType
from retry import retry
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
        :param json_output: output json (as dictionary)
        :param keys_to_search_for: list of keys to search for
        :param should_be_found: True if key_str_to_search_for should be found in the output. False - otherwise
        :return: ResultObj
        """
        with allure.step('Verify field `{field}` {exist} in json output'.format(field=keys_to_search_for,
                                                                                exist="exists" if should_be_found else "doesn't exist")):
            result_obj = ResultObj(result=True, info="", issue_type=IssueType.PossibleBug)
            if not keys_to_search_for or len(keys_to_search_for) == 0:
                result_obj.result = False
                result_obj.info = "Invalid input"
                result_obj.issue_type = IssueType.TestIssue
                return result_obj

            result_obj.info = ""
            nested_list = []
            for nested_dict_key in ValidationTool._get_all_keys(json_output):
                nested_list.append(nested_dict_key)
            for key in keys_to_search_for:
                if key in json_output.keys() or key in nested_list:
                    if should_be_found:
                        logging.info("'{str_to_search_for}' field was found".format(str_to_search_for=key))
                    else:
                        result_obj.result = False
                        result_obj.info += "'{str_to_search_for}' field was found while it should not\n".format(
                            str_to_search_for=key)
                else:
                    if should_be_found:
                        result_obj.result = False
                        result_obj.info += "'{str_to_search_for}' field was not found\n".format(str_to_search_for=key)
                    else:
                        logging.info("'{str_to_search_for}' field was not found as expected".format(str_to_search_for=key))

            return result_obj

    @staticmethod
    def _get_all_keys(json_output):
        for key, value in json_output.items():
            yield key
            if isinstance(value, dict):
                yield from ValidationTool._get_all_keys(value)

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

            if str(output_dictionary[field_name]).strip() == str(expected_value).strip():
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
    @retry(Exception, tries=2, delay=2)
    def validate_fields_values_in_output(expected_fields, expected_values, output_dict):
        """

        :param expected_fields: list of expected fields
        :param expected_values: list of expected values
        :param output_dict: output
        :return:
        """
        with allure.step("Verify existence of all components in the output dict"):
            if not output_dict:
                return ResultObj(False, "The list is empty")

            result = True
            ret_info = ""
            for field, value in zip(expected_fields, expected_values):
                result_obj = ValidationTool.verify_field_value_in_output(output_dict, field, value)
                if not result_obj.result:
                    result = False
                    ret_info += result_obj.info

            return ResultObj(result, ret_info, ret_info)

    @staticmethod
    def compare_values(value1, value2, should_equal=True):
        """
        Compares two values
        :param value1: first value
        :param value2: second value
        :param should_equal: True of False
        :return: ResultObj - while ResultObj.returned_value = True if the values are equal, False - otherwise
        """
        result_obj = ResultObj(False, "")
        if value1 == value2:
            result_obj = ResultObj(True, "The values are equal", True) if should_equal else \
                ResultObj(False, "The values are equal while they shouldn't", False)
        else:
            result_obj = ResultObj(True, "The values are not equal as expected", True) if not should_equal else \
                ResultObj(False, "The values are not equal while they should", False)
        return result_obj

    @staticmethod
    def verify_all_fields_value_exist_in_output_dictionary(output_dictionary, expected_fields,
                                                           check_empty_values=True):
        with allure.step('Verify all the fields values are not None and includes all expected fields'):

            result_obj = ResultObj(result=True, info="", issue_type=IssueType.PossibleBug)

            if not all(field in list(output_dictionary.keys()) for field in expected_fields):
                result_obj.result = False
                result_obj.info += "the next fields are missing on the device constants {missing} ".format(
                    missing=list(set(output_dictionary.keys()) ^ set(expected_fields)))

            if not all(field in expected_fields for field in list(output_dictionary.keys())):
                result_obj.result = False
                result_obj.info += "the next fields are missing on the cmd output {missing}".format(
                    missing=expected_fields - output_dictionary.keys())

            if check_empty_values:
                for key, value in output_dictionary.items():
                    if not value:
                        result_obj.result = False
                        result_obj.info += "The value of {field_name} is None".format(field_name=key)
            return result_obj

    @staticmethod
    def verify_field_value_exist_in_output_dict(output_dict, expected_fields):
        """
        :param expected_fields: list of expected fields
        :param output_dict: output
        :return:
        """
        with allure.step("Verify existence of the fields in the output dict"):
            if not output_dict:
                return ResultObj(False, "The list is empty")

            result = True
            ret_info = ""
            if expected_fields not in output_dict.keys():
                ret_info += 'the {field} not found\n'.format(field=field)
                result = False

            return ResultObj(result, ret_info, ret_info)

    @staticmethod
    def compare_dictionaries(first_dictionary, second_dictionary, ignore_double_quotes_in_values=False):
        """
        Compares two dictionaries
        @param first_dictionary: the first dictionary
        @param second_dictionary: the second dictionary
        @param ignore_double_quotes_in_values: if True - ignore double quotes in value comparison
            e.g: if True, { "key" = val } and { "key": "val" } are the same.
        """
        if set(first_dictionary.keys()) == set(second_dictionary.keys()):
            for key in first_dictionary.keys():
                if first_dictionary[key] != second_dictionary[key]:
                    if ignore_double_quotes_in_values:
                        v1, v2 = str(first_dictionary[key]), str(second_dictionary[key])
                        v1 = v1[1:-1] if v1.startswith('\"') and v1.endswith('\"') else v1
                        v2 = v2[1:-1] if v2.startswith('\"') and v2.endswith('\"') else v2
                        if v1 != v2:
                            return ResultObj(False, "'{}' are not equal for both dictionaries.\nvalue1: {}\tvalue2: {}"
                                             .format(key, first_dictionary[key], second_dictionary[key]))
                    else:
                        return ResultObj(False, "'{}' are not equal for both dictionaries.\nvalue1: {}\tvalue2: {}"
                                         .format(key, first_dictionary[key], second_dictionary[key]))
            return ResultObj(True, "The dictionaries are equal")
        return ResultObj(False, "The dictionaries are not equal")

    @staticmethod
    def verify_substring_in_output(output, substring, err_message_in_case_of_failure, should_be_found=False):
        """
        :param output: string command output
        :param substring:
        :param err_message_in_case_of_failure: the error message
        :param should_be_found: True if you want to check substring not in output,
                       False if you want to check substring in output
        :return:
        """
        if should_be_found:
            with allure.step('check if command output contains {substring}'.format(substring=substring)):
                assert substring in output, err_message_in_case_of_failure
        else:
            with allure.step('check if command output does not contain {substring}'.format(substring=substring)):
                assert substring not in output, err_message_in_case_of_failure

    @staticmethod
    def validate_all_values_exists_in_list(expected_values_list, output_list):
        with allure.step("Verify existence of all components in the output list"):
            if not output_list:
                return ResultObj(False, "The list is empty")

            ret_info = ""
            for comp in expected_values_list:
                if comp in output_list:
                    logging.info("'{}' found\n")
                else:
                    ret_info += "'{}' + cant be found\n".format(comp)

            return ResultObj(not ret_info, ret_info)

    @staticmethod
    def compare_dictionary_content(output_dictionary, sub_dictionary):
        with allure.step("Verify the sub dictionary can be found in the output"):
            info = ""
            output_dictionary_keys = output_dictionary.keys()
            for key, value in sub_dictionary.items():
                if key not in output_dictionary_keys:
                    info += key + " can't be found in output dictionary\n"
                elif value != output_dictionary[key]:
                    info += "the value of {} is not equal in both dictionaries\n".format(key)

            return ResultObj(not info, info)

    @staticmethod
    def compare_nested_dictionary_content(output_dictionary, sub_dictionary):
        with allure.step("Verify the sub nested dictionary can be found in the output"):
            info = ""
            output_dictionary_keys = output_dictionary.keys()
            for key, value in sub_dictionary.items():
                if key not in output_dictionary_keys:
                    info += key + " can't be found in output dictionary\n"
                else:
                    if isinstance(output_dictionary[key], dict) and isinstance(sub_dictionary[key], dict):
                        res = ValidationTool.compare_nested_dictionary_content(output_dictionary[key],
                                                                               sub_dictionary[key])
                        if not res.result:
                            return res
                    elif value != output_dictionary[key]:
                        info += "the value of {} is not equal in both dictionaries\n".format(key)

            return ResultObj(not info, info)

    @staticmethod
    def verify_sub_strings_in_str_output(str_output, req_fields):
        if any(field not in str_output for field in req_fields):
            return ResultObj(False, "Not all required fields were found")
        return ResultObj(True)

    @staticmethod
    def verify_all_files_in_compressed_folder(engine, zipped_folder_name, files_list, zipped_folder_path="", path=""):
        """
        :param engine:
        :param zipped_folder_name:
        :param files_list:
        :param zipped_folder_path:
        :param path:
        :return:
        """
        with allure.step('Validate all expected files are exist in the compressed folder{}'.format(zipped_folder_name)):
            with allure.step('Get files list in compressed folder'):
                engine.run_cmd('sudo tar -xf ' + zipped_folder_path + '/' + zipped_folder_name + ' -C ' + zipped_folder_path)
                output = engine.run_cmd('ls ' + zipped_folder_path + path).split()
                engine.run_cmd('sudo rm -rf ' + zipped_folder_path + '/' + path.split('/')[1])

            with allure.step('Validate that all expected files are exist and nothing more'):
                files = [file for file in output if file not in files_list]
                if len(files):
                    return ResultObj(False, "the next files are missed {files}".format(files=files))

                files = [file for file in files_list if file not in output]
                if len(files):
                    logger.warning(
                        "the next files are in the dump folder but not in our check list {files}".format(files=files))

            return ResultObj(True, "all expected files are exist", True)

    @staticmethod
    def get_dictionaries_diff(dict1, dict2):
        difference = {}

        for key, value in dict1.items():
            if key not in dict2:
                difference[key] = value
            elif isinstance(value, dict) and isinstance(dict2[key], dict):
                nested_difference = ValidationTool.get_dictionaries_diff(value, dict2[key])
                if nested_difference:
                    difference[key] = nested_difference

        return difference

    @staticmethod
    def has_key_with_value(dictionary, req_key, req_val):
        if req_key in dictionary.keys() and dictionary[req_key] == req_val:
            return True
        for key, value in dictionary.items():
            if isinstance(value, dict) and ValidationTool.has_key_with_value(value, req_key, req_val):
                return True
        return False