from ngts.nvos_tools.infra.ResultObj import ResultObj, IssueType

invalid_cmd_str = ['invalid date', 'Invalid config', 'Error', 'command not found', 'Bad Request', 'Not Found',
                   "unrecognized arguments", "error: unrecognized arguments", "invalid choice", "Action failed",
                   "Invalid Command", "You do not have permission", "Incomplete Command", "Unable to change",
                   'internal error occurred', 'Valid range is']
timeout_cmd_str = ['Timeout while waiting for client response']


class SendCommandTool:

    @staticmethod
    def verify_cmd_execution(cmd_output, expected_str=""):
        """
        Check executed command output and return a ResultObj
        """
        if cmd_output:

            if expected_str and expected_str in cmd_output:
                return ResultObj(True, "", str(cmd_output))

            if any(err_msg in str(cmd_output) for err_msg in invalid_cmd_str):
                return ResultObj(False, "Command failed with the following output: \n" + str(cmd_output), None,
                                 IssueType.PossibleBug)
            if any(timeout_msg in str(cmd_output) for timeout_msg in timeout_cmd_str):
                return ResultObj(False, "Timeout occurred with the following output: \n" + str(cmd_output), None,
                                 IssueType.TestIssue)

        return ResultObj(expected_str == "", "Got empty output but expected: {}".format(expected_str), str(cmd_output))

    @staticmethod
    def execute_command_expected_str(command_to_execute, expected_str, *args):
        output = command_to_execute(*args)
        return SendCommandTool.verify_cmd_execution(output, expected_str)

    @staticmethod
    def execute_command(command_to_execute, *args):
        """
        Execute the 'command_to_execute' and check the output
        :param command_to_execute: method to call
        :return: ResultObj
        """
        if not command_to_execute:
            return ResultObj(False, "Command to execute was not provided", None, IssueType.TestIssue)

        output = command_to_execute(*args)
        return SendCommandTool.verify_cmd_execution(output)
