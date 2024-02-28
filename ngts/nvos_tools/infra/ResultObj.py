import logging


class IssueType:
    Unknown = 0
    TestIssue = 1
    PossibleBug = 2

    exception_msg = {Unknown: "", TestIssue: "*** POSSIBLE TEST ISSUE ***\n", PossibleBug: "*** POSSIBLE BUG ***\n"}


class ResultObj:
    result = False
    info = ""
    returned_value = None
    issue_type = IssueType.Unknown

    def __init__(self, result, info="", returned_value=None, issue_type=IssueType.Unknown):
        self.result = result
        self.info = info
        self.returned_value = returned_value
        self.issue_type = issue_type

    def verify_result(self, should_succeed=True):
        """
        Assert an error if result is False, otherwise returns returned_value
        :return: If 'result' is True, returns the 'returned_value'
        """
        logging.info("\n   Result: {result}\n   should_succeed: {should_succeed}\n   info: {info}\n".format(
                     result='True' if self.result else 'False',
                     should_succeed='True' if should_succeed else 'False',
                     info=self.info))
        self.info = IssueType.exception_msg[self.issue_type] + self.info

        if should_succeed:
            assert self.result, self.info if self.info else "The operation failed"
        else:
            assert not self.result, self.info if self.info else "The operation succeeded while it is expected to fail"

        return self.returned_value if self.returned_value else self.info
        # todo return self.returned_value if self.result else self.info

    def get_returned_value(self, should_succeed=True):
        return self.verify_result(should_succeed)
