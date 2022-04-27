from ngts.nvos_tools.infra.ResultObj import ResultObj, IssueType

invalid_cmd_str = ['Invalid config', 'Error', 'command not found']
timeout_cmd_str = ['Timeout while waiting for client response']


class SendCommandTool:

    @staticmethod
    def verify_cmd_execution(cmd_output):
        """
        Check executed command output and return a ResultObj
        """
        if cmd_output:
            for cmd_str in invalid_cmd_str:
                if cmd_str in cmd_output:
                    return ResultObj(False, "Command failed with the following output: \n" + cmd_output, None,
                                     IssueType.PossibleBug)
            for cmd_str in timeout_cmd_str:
                if cmd_str in cmd_output:
                    return ResultObj(False, "Timeout occurred with the following output: \n" + cmd_output, None,
                                     IssueType.TestIssue)
        return ResultObj(True, "", cmd_output)

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
