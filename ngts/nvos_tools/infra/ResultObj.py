class ResultObj:
    result = False
    info = ""
    returned_value = None

    def __init__(self, result, info, returned_value=None):
        self.result = result
        self.info = info
        self.returned_value = returned_value

    def verify_result(self, should_succeed=True):
        """
        Assert an error if result is False, otherwise returns returned_value
        :return: If 'result' is True, returns the 'returned_value'
        """
        assert (should_succeed and self.result) or (not should_succeed and not self.result), self.info
        return self.returned_value

    def get_returned_value(self, should_succeed=True):
        return self.verify_result(should_succeed)
