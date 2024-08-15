import pprint

from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain import hub

from module.customStructuredTool import CustomStructuredTool
from utils import get_UID, send_email, get_weiboInfo, EmailInput, extract_UID
import os
os.environ['http_proxy'] = '127.0.0.1:7897'
os.environ['https_proxy'] = '127.0.0.1:7897'
os.environ['SERPAPI_API_KEY'] = ''

if __name__ == "__main__":
    # 任务模板 对输入的搜索内容 query 获取一个微博用户UID
    # 查询数据库是否有相关合作记录
    # 利用UID获取用户的详细资料，并根据资料生成合作文案
    # 利用工具发送邮件

    template = """
    The first step, I want you to obtain the 微博 UID related to {}. So when you search, you should focus on searching for Weibo data
    If the UID is not found, you can try adding more keywords after the search term multiple times.
    For example, if you want to search for 玩具, you can enter "玩具 微博" or "玩具 Weibo" when using the tool, and so on
    For this task, your answer should only have one UID. 
    UID generally exists in a segment of URL, which is composed of https://weibo.com/u/ or https://m.weibo.cn/u/ start 
    for example there is currently a URL of https://weibo.com/u/1234567890 or https://m.weibo.cn/u/1234567890 So 1234567890 is the UID I need
    The second step, After obtaining the UID, use this UID to search for the detailed information,
    You need to get the email address from the detailed information, email address example: email@example.com
    If you cannot obtain the email address from the detailed information, you need to go back to the first step and search again to find a new UID 
    The third step, I want you send an email to this email address,sender is 1025506394@qq.com. 
    The content of the email needs to be generated based on the detailed information obtained above and in chinese,
    and it consists of two parts: first, indicate that you are his fan based on his detailed information, 
    and expressing appreciation for him, then further indicate that my company wants to cooperate with him.
    Please complete step by step.
                  """
    # query = input("请输入搜索内容：")
    # 初始化AI大模型
    llm = ChatOllama(model="llama3")
    # llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-1106", openai_api_key = "sk-", streaming=True)
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
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt)
    #限制迭代次数
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, max_iterations=15)
    agent_executor.invoke({"input": template.format("牡丹")})

    for step in agent_executor.iter({"input": template.format("牡丹")}):
        print("step:", step)

    # chunks = []
    # for chunk in agent_executor.stream(
    #         {"input": template.format("宠物")}
    # ):
    #     chunks.append(chunk)
    #     print("------")
    #     pprint.pprint(chunk, depth=2)