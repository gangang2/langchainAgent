import operator
import pprint
from typing import TypedDict, Annotated, Sequence, Union

from langchain_community.chat_models import ChatOllama
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_core.utils.function_calling import format_tool_to_openai_function
from langchain_openai import ChatOpenAI
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain import hub
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor

from module.customStructuredTool import CustomStructuredTool
from utils import get_UID, send_email, get_weiboInfo, EmailInput, extract_UID

# os.environ['http_proxy'] = '127.0.0.1:7897'
# os.environ['https_proxy'] = '127.0.0.1:7897'
# os.environ['SERPAPI_API_KEY'] = '63fadc9b8ef4dd06d1ef3daff72bfaeb114a3a4116b6e484058fb9a07476c7a2'

class AgentState(TypedDict):
   # The list of previous messages in the conversation
   chat_history: list[BaseMessage]
   # The outcome of a given call to the agent
   # Needs `None` as a valid type, since this is what this will start as
   agent_outcome: Union[AgentAction, AgentFinish, None]
   # List of actions and corresponding observations
   # Here we annotate this with `operator.add` to indicate that operations to
   # this state should be ADDED to the existing values (not overwrite it)
   intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]
   # The input string
   input: str

# 任务模板
# 对输入的搜索内容 query 获取一个微博用户UID
# 利用UID获取用户的详细资料，并根据资料生成合作文案
# 利用工具向该用户发送邮件

template = """
    Your ultimate task is to use the obtained UID to obtain an email address, and then send an email to this address.
    Now, complete the task step by step.
    The first step, I want you to obtain the 微博 UID related to {}. So when you search, you should focus on searching for Weibo data
    If the UID is not found, you can try adding more keywords after the search term multiple times.
    For example, if you want to search for 玩具, you can enter "玩具 微博" or "玩具 Weibo" when using the tool, and so on
    For this task, your answer should only have one UID. 
    UID generally exists in a segment of URL, which is composed of https://weibo.com/u/ or https://m.weibo.cn/u/ start 
    for example there is currently a URL of https://weibo.com/u/1234567890 or https://m.weibo.cn/u/1234567890 So 1234567890 is the UID I need
    The second step, After obtaining the UID, use this UID to search for the detailed information,
    You need to get the email address from the detailed information
    If you cannot obtain the email address from the detailed information, you need to go back to the first step and search again to find a new UID 
    If you have obtained the email address, proceed to the third step
    The third step, I want you using email tools to send an email to this email address,sender is 1025506394@qq.com. 
    The content of the email needs to be generated based on the detailed information obtained above and in chinese,
    and it consists of two parts: first, indicate that you are his fan based on his detailed information, 
    and expressing appreciation for him, then further indicate that my company wants to cooperate with him
              """

# 初始化AI大模型
llm = ChatOllama(model="llama3")

# 开启 工具异常处理 handle_tool_error = true 也可以自定义方式来处理工具错误 handle_tool_error = _handle_error
send_email_tool = CustomStructuredTool.from_function(
    func=send_email,
    name="send_email",
    description="用于发送邮件",
    args_schema=EmailInput,
    return_direct=True,
    handle_tool_error=True,
)

tools = [Tool(func=get_UID, name="get_UID", description="用于搜索获取网络页面数据")
    ,Tool(func=get_weiboInfo, name="get_weiboInfo", description="输入UID来获取该用户的详细信息")
    ,send_email_tool
]

## 工具执行处理器
tool_executor = ToolExecutor(tools)
prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt)

def call_model(state: AgentState):
    print("call_model state:", str(state))
    agent_outcome = agent.invoke(state)
    print("call_model agent_outcome:", str(agent_outcome))
    return {"agent_outcome": agent_outcome}

def tool_execute(state: AgentState):
    print("tool_execute state:", str(state))
    agent_action = state["agent_outcome"]
    output = tool_executor.invoke(agent_action)
    print("tool_execute output:", str(output))
    return {"intermediate_steps": [(agent_action, output)]}

def should_continue(state: AgentState):
    if isinstance(state["agent_outcome"], AgentFinish) or len(state["intermediate_steps"]) > 6:
        return "end"
    return "continue"

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_execute)
workflow.add_conditional_edges("agent", should_continue, {"end": END, "continue": "action"})
workflow.add_edge("action", "agent")
workflow.set_entry_point("agent")
app = workflow.compile()
input_data = {"input": template.format("牡丹"), "intermediate_steps": [], "chat_history": []}
print(input_data)
config = {"configurable": {"thread_id": "test_thread1"}}
for s in app.stream(input_data, config):
    print(list(s.values())[0])
    print("---------")
