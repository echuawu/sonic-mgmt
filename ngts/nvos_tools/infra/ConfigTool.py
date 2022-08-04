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
