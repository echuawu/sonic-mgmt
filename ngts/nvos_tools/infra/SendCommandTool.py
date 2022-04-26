from ngts.nvos_tools.infra.ResultObj import ResultObj, IssueType

invalid_cmd_str = ['Invalid config', 'Error', 'Failed']


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
        return ResultObj(True, "", cmd_output)

    @staticmethod
    def execute_command(engine, command_to_execute, user_input, *args):
        """
        Execute the 'command_to_execute' and check the output
        :param engine: ssh dut engine
        :param command_to_execute: method to call
        :param user_input: user input if needed
        :return: ResultObj
        """
        if not command_to_execute:
            return ResultObj(False, "Command to execute was not provided", None, IssueType.TestIssue)

        output = command_to_execute(*args)
        result_obj = SendCommandTool.verify_cmd_execution(output)

        if result_obj.result and user_input:
            output = engine.run_cmd(user_input)
            result_obj = SendCommandTool.verify_cmd_execution(output)
            result_obj.returned_value = output

        return result_obj
