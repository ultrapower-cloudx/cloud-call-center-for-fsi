"""
tool execute format
"""

from common_logic.common_utils.constant import (
    LLMModelType,
    MessageType
)

class FormatMeta(type):
    def __new__(cls, name, bases, attrs):
        new_cls = type.__new__(cls, name, bases, attrs)

        if name == "FormatToolResult":
            return new_cls
        new_cls.model_map[new_cls.model_id] = new_cls
        return new_cls
    

class FormatToolResult(metaclass=FormatMeta):
    model_map = {}

    @classmethod
    def format(cls,model_id,tool_output:dict):
        target_cls = cls.model_map[model_id]
        return target_cls.format(tool_output)
        

CLAUDE_TOOL_EXECUTE_SUCCESS_TEMPLATE = """
<function_results>
<result>
<tool_name>{tool_name}</tool_name>
<stdout>
{result}
</stdout>
</result>
</function_results>
"""

CLAUDE_TOOL_EXECUTE_FAIL_TEMPLATE = """
<function_results>
<error>
{error}
</error>
</function_results>
"""

MIXTRAL8X7B_TOOL_EXECUTE_SUCCESS_TEMPLATE = """工具: {tool_name} 的执行结果如下:
{result}"""

MIXTRAL8X7B_TOOL_EXECUTE_FAIL_TEMPLATE = """工具: {tool_name} 执行错误，错误如下:
{error}"""

class Claude3SonnetFormatToolResult(FormatToolResult):
    model_id = LLMModelType.CLAUDE_3_SONNET
    execute_success_template = CLAUDE_TOOL_EXECUTE_SUCCESS_TEMPLATE
    execute_fail_template = CLAUDE_TOOL_EXECUTE_FAIL_TEMPLATE
    
    @classmethod
    def format_one_tool_output(cls,tool_output:dict):
        exe_code = tool_output['code']
        if exe_code == 1:
            # failed
            return cls.execute_fail_template.format(
                error=tool_output['result'],
                tool_name = tool_output['tool_name']
            )
        elif exe_code == 0:
            # succeed
            return cls.execute_success_template.format(
                tool_name=tool_output['tool_name'],
                result=tool_output['result']
            )
        else:
            raise ValueError(f"Invalid tool execute: {tool_output}") 
    
    @classmethod
    def format(cls,tool_call_outputs:list[dict]):
        tool_call_result_strs = []
        for tool_call_result in tool_call_outputs:
            tool_exe_output = tool_call_result['output']
            if 'name' in tool_call_result.keys():
                tool_exe_output['tool_name'] = tool_call_result['name']
            ret:str = cls.format_one_tool_output(
                tool_exe_output
            )
            tool_call_result_strs.append(ret)
        
        ret = "\n".join(tool_call_result_strs)
        return {
            "tool_message": {
                "role": MessageType.HUMAN_MESSAGE_TYPE,
                "content": ret,
                "additional_kwargs": {
                    "original": [out['output'] for out in tool_call_outputs],
                    "raw_tool_call_results": tool_call_outputs,
                    },
            }
        }

class Claude3HaikuFormatToolResult(Claude3SonnetFormatToolResult):
    model_id = LLMModelType.CLAUDE_3_HAIKU


class Claude35SonnetFormatToolResult(Claude3SonnetFormatToolResult):
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"


class Claude2FormatToolResult(Claude3SonnetFormatToolResult):
    model_id = LLMModelType.CLAUDE_2


class Claude21FormatToolResult(Claude3SonnetFormatToolResult):
    model_id = LLMModelType.CLAUDE_21


class ClaudeInstanceFormatToolResult(Claude3SonnetFormatToolResult):
    model_id = LLMModelType.CLAUDE_INSTANCE


class Mixtral8x7bFormatToolResult(Claude3SonnetFormatToolResult):
    model_id = LLMModelType.MIXTRAL_8X7B_INSTRUCT
    execute_success_template = MIXTRAL8X7B_TOOL_EXECUTE_SUCCESS_TEMPLATE
    execute_fail_template = MIXTRAL8X7B_TOOL_EXECUTE_FAIL_TEMPLATE


class GLM4Chat9BFormatToolResult(FormatToolResult):
    model_id = LLMModelType.GLM_4_9B_CHAT
    
    @classmethod
    def format(cls,tool_call_outputs:list[dict]):
        tool_call_result_strs = []
        for tool_call_result in tool_call_outputs:
            tool_exe_output = tool_call_result['output']
            tool_call_result_strs.append(str(tool_exe_output['result']))
        # print(tool_exe_output['result'])
        ret = "\n".join(tool_call_result_strs)
        return {
            "tool_message": {
                "role": MessageType.TOOL_MESSAGE_TYPE,
                "content": ret,
                "additional_kwargs": {
                    "original": [out['output'] for out in tool_call_outputs],
                    "raw_tool_call_results":tool_call_outputs,
                    },
            }
        }

class Qwen2Instruct7BFormatToolResult(FormatToolResult):
    model_id = LLMModelType.QWEN2INSTRUCT7B
    FN_RESULT = '✿RESULT✿'
    FN_EXIT = '✿RETURN✿'

    @classmethod
    def format(cls,tool_call_outputs:list[dict]):
        tool_call_result_strs = []
        for tool_call_result in tool_call_outputs:
            tool_exe_output = tool_call_result['output']
            result = tool_exe_output["result"]
            tool_call_result_strs.append(f'\n{cls.FN_RESULT}: {result}\n{cls.FN_EXIT}:')
        
        ret = "\n".join(tool_call_result_strs)
        return {
            "tool_message": {
                "role": MessageType.TOOL_MESSAGE_TYPE,
                "content": ret,
                "additional_kwargs": {
                    "original": [out['output'] for out in tool_call_outputs],
                    "raw_tool_call_results":tool_call_outputs,
                    },
            }
        }


class Qwen2Instruct72BFormatToolResult(Qwen2Instruct7BFormatToolResult):
    model_id = LLMModelType.QWEN2INSTRUCT72B


class QWEN15INSTRUCT32BFormatToolResult(Qwen2Instruct7BFormatToolResult):
    model_id = LLMModelType.QWEN15INSTRUCT32B


format_tool_call_results = FormatToolResult.format



        






