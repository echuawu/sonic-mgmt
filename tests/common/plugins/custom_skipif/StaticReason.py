import logging

from CustomSkipIf import CustomSkipIf

logger = logging.getLogger()


class SkipIf(CustomSkipIf):
    def __init__(self, ignore_list, pytest_item_obj):
        super(SkipIf, self).__init__(ignore_list, pytest_item_obj)
        self.name = 'StaticReason'

    def is_skip_required(self, skip_dict_result):
        """
        Make decision about ignore - is it required or not
        :param skip_dict_result: shared dictionary with data about skip test
        :return: updated skip_dict
        """
        if self.ignore_list:
            skip_dict_result[self.name] = self.ignore_list

        return skip_dict_result
