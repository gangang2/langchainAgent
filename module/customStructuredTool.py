from langchain_core.tools import StructuredTool
from typing import Union, Dict, Any

from utils import convert_to_dict


class CustomStructuredTool(StructuredTool):
    def _parse_input(
        self,
        tool_input: Union[str, Dict],
    ) -> Union[str, Dict[str, Any]]:
        """Convert tool input to pydantic model."""

        print("myPareInput:", tool_input, type(tool_input))
        input_args = self.args_schema
        new_tool_input = convert_to_dict(tool_input)
        if new_tool_input is not None:
            tool_input = new_tool_input

        print("myPareInput:", new_tool_input, type(new_tool_input), tool_input, type(tool_input))
        if isinstance(tool_input, str):
            if input_args is not None:
                key_ = next(iter(input_args.__fields__.keys()))
                print("tool_input:", tool_input, "key_:", key_)
                input_args.validate({key_: tool_input})
            return tool_input
        else:
            if input_args is not None:
                result = input_args.parse_obj(tool_input)
                return {
                    k: getattr(result, k)
                    for k, v in result.dict().items()
                    if k in tool_input
                }
        return tool_input