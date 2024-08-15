这是由langchain实现的简易广告合作Demo，

输入关键词，实现从微博上搜索关键词相关领域的博主，解析博主的个人信息，

获取合作邮箱后，发送合作邮件，全程由langchain Agent实现自动化。

流程：prompt上将上述流程用英语写好（代码里调用本地部署的LLama3模型，该模型对中文支持较弱，无法很好理解中文描述的任务），

使用pydantic定义工具的多参数输入，将写好【搜索引擎工具，爬虫工具，发送邮件工具】将工具信息提供给agent，最终将agent交由给AgentExecutor执行。

优化：
1.使用openAI的gpt3.5或者4.0可以正常完成。如果使用本地部署的qwen或者llama3 在涉及到微博信息获取的时候，检查到爬虫是风险操作，会拒绝执行，

所以我们可以尝试对模型进行安全审查的切除，切除后就可以正常执行我们的任务了，不过由于消融了大模型的拒绝方向，在涉及到政治，网络攻击等敏感问题不再拒绝回答，

也会给出答案，这个时候就可以考虑加入nemoGuardRails完全审查框架。

这个是我在colab对qwen小参数模型微调消融模型拒绝方向的笔记，可以按这个笔记一步一步操作执行（https://colab.research.google.com/drive/14OJlgijR1y1Yxxw8MnhgQjzBxeLwx0gQ?usp=sharing）。

2.langchain的agentExecutor在实际运行中是黑盒状态，为了增强可控性，实现任务流程的编排，例如在流程执行的时候，强制先执行设定的某些工具，
可使用langgraph，用langgraph提供的【图的执行能力】来实现agentExecutor里的工具执行流程，也方便引入多代理，扩展出多代理协作和决策反省等。


![37b3d1dc5a47c64781afb16cb064b32](https://github.com/user-attachments/assets/3ba848c7-895c-4daa-8a18-1c9d38e1981b)
