from ngts.nvos_tools.infra.ResultObj import ResultObj, IssueType

invalid_cmd_str = ['Invalid config', 'Error', 'command not found', 'Bad Request', 'Not Found', "unrecognized arguments",
                   "error: unrecognized arguments", "invalid choice", "Action failed"]
timeout_cmd_str = ['Timeout while waiting for client response']


class SendCommandTool:

    @staticmethod
    def verify_cmd_execution(cmd_output, success_str=""):
        """
        Check executed command output and return a ResultObj
        """
        if cmd_output:

            if success_str and success_str in cmd_output:
                return ResultObj(True, "", str(cmd_output))

            for err_msg in invalid_cmd_str:
                if err_msg in str(cmd_output):
                    return ResultObj(False, "Command failed with the following output: \n" + str(cmd_output), None,
                                     IssueType.PossibleBug)
            for timeout_msg in timeout_cmd_str:
                if timeout_msg in str(cmd_output):
                    return ResultObj(False, "Timeout occurred with the following output: \n" + str(cmd_output), None,
                                     IssueType.TestIssue)

        return ResultObj(True, "", str(cmd_output))

    @staticmethod
    def execute_command_success_str(command_to_execute, success_str, *args):
        output = command_to_execute(*args)
        return SendCommandTool.verify_cmd_execution(output, success_str)

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
