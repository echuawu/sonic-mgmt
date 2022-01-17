from CustomSkipIf import CustomSkipIf
from ngts.tools.redmine.redmine_api import is_redmine_issue_active


class SkipIf(CustomSkipIf):
    def __init__(self, ignore_list, pytest_item_obj):
        super(SkipIf, self).__init__(ignore_list, pytest_item_obj)
        self.name = 'Redmine'

    def is_skip_required(self, skip_dict):
        is_issue_active, issue_id = is_redmine_issue_active(self.ignore_list)
        if is_issue_active:
            issue_url = 'https://redmine.mellanox.com/issues/{}'.format(issue_id)
            skip_dict[self.name] = issue_url

        return skip_dict
