import logging
import json
import allure
from .ResultObj import ResultObj
logger = logging.getLogger()


class ConfigTool:

    @staticmethod
    def read_from_history(history_list, apply_order, label_to_read):
        """
        after running nv config history and parsing using parse_config_history
        you can use this method to read a specific label value

        :param history_list: history
        :param apply_order: the apply order - 0 if you want to read the last apply history labels
        :param label_to_read: label to read -
                        could be [apply-id, method, reason, rev_id, state_controls, user, date, message, ref]
        :return:
        """
        if len(history_list) == 0:
            ResultObj(True, 'the applies history is empty', '')
        if apply_order < 0 or apply_order > len(history_list) - 1:
            return ResultObj(False, '', 'history id is out of range, should be between 0 and {len}'.
                             format(len=len(history_list)))
        if label_to_read not in history_list[apply_order].keys():
            return ResultObj(False, '', 'no label name {label_name}'.format(label_name=label_to_read))

        return ResultObj(True, '', history_list[apply_order][label_to_read])

    @staticmethod
    def verify_diff_after_config(diff_output, operation, resource_path, value=''):
        """
        after set/unset operations without apply you can use this method to verify
        that diff config output includes the expected values using the resource path
        for example
            after running nv set system hostname
            diff output should be:
                set:{
                    'system':{
                            'hostname = <new_hostname>
                            }
                    }

        :param diff_output: the output after running nv config diff --output =json
        :param resource_path: path (example : system/hostname
        :param operation: set or unset
        :param value: the change value if operation = set
        :return: True if the diff output includes the expected path and value
        """
        if diff_output == '{}' or not diff_output:
            return ResultObj(bool(operation), "", {})
        with allure.step('Verify diff config includes the resource change'):
            diff_dictionary = json.loads(diff_output)[0]
            path = resource_path.split('/')
            with allure.step('Verify diff config content the {opt}'.format(opt=operation)):
                if operation not in diff_dictionary.keys():
                    return ResultObj(False, '', 'the diff output should include {label}'.format(label=operation))
            partial_diff_output = diff_dictionary[operation]
            with allure.step('Verify diff config content the resource path {path}'.format(path=path)):
                for label in path:
                    if label not in partial_diff_output.keys():
                        return ResultObj(False, '', 'the diff output should include {label}'.format(label=label))
                    partial_diff_output = partial_diff_output[label]
            with allure.step('Verify diff config content the change {value}'.format(value=value)):
                if operation == 'set' and partial_diff_output != value:
                    return ResultObj(False, '', 'the set value should be {label}'.format(label=value))
                return ResultObj(True, '', '')

    @staticmethod
    def verify_show_after_apply(show_output, operation, resource_path, value=''):
        """
        after set/unset operations with apply you can use this method to verify
        that show config output includes the expected values using the resource path
        for example
            after running nv set system hostname (apply=True)
            show output should be:
                set:{
                    'system':{
                            'hostname = <new_hostname>
                            }
                    }

        :param show_output: the output after running nv config show --output =json
        :param resource_path: path (example : system/hostname
        :param operation: set or unset
        :param value: the change value if operation = set
        :return True if the show output includes the expected path and value
        """
        if show_output == '{}' or not show_output:
            return ResultObj(bool(operation), "", {})
        with allure.step('Verify show config includes the resource change'):
            diff_dictionary = json.loads(show_output)[0]
            path = resource_path.split('/')
            with allure.step('Verify show config content the {opt}'.format(opt=operation)):
                if operation not in diff_dictionary.keys():
                    return ResultObj(False, '', 'the diff output should include {label}'.format(label=operation))
            partial_diff_output = diff_dictionary[operation]
            with allure.step('Verify show config content the resource path {path}'.format(path=path)):
                for label in path:
                    if label not in partial_diff_output.keys():
                        return ResultObj(False, '', 'the diff output should include {label}'.format(label=label))
                    partial_diff_output = partial_diff_output[label]
            with allure.step('Verify show config content the change {value}'.format(value=value)):
                if operation == 'set' and partial_diff_output != value:
                    return ResultObj(False, '', 'the set value should be {label}'.format(label=value))
                return ResultObj(True, '', '')
