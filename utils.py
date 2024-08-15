import json
import time

import requests
from langchain.pydantic_v1 import BaseModel, Field
import os

from langchain_core.tools import ToolException

from module.customSerpApiWrapper import CustomSerpAPIWrapper
import re
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from typing import Union, Dict, Any
import ast

os.environ['infobip_api_key'] = ''
os.environ['infobip_base_url'] = 'https://mm4jd2.api.infobip.com'
# os.environ['http_proxy'] = '127.0.0.1:7897'
# os.environ['https_proxy'] = '127.0.0.1:7897'
os.environ['SERPAPI_API_KEY'] = ''

weibo_cookies = '''SINAGLOBAL=1978161670827.5452.1715522949436; UOR=,,www.google.com; _s_tentry=-; Apache=7790137705630.064.1720082445025; ULV=1720082445061:2:1:1:7790137705630.064.1720082445025:1715522949466; XSRF-TOKEN=Xul-CPs7Wgx-22V7HLDKvmyM; SCF=Aq7u-NvN6RZO4ppXK64h8OWV_qjk0PpFksVnHOuj-ZaHEMaUsJJaoNGjrB9Cv1rldYdxpXOOkCxqu7fd1R-BgFo.; ALF=1723960852; SUB=_2A25LnnFEDeRhGeBM7lIR9i_Kyj2IHXVo0oyMrDV8PUJbkNAbLWX2kW1NRNAaES_O6cDvDTRrYx0q60daT8vRUrve; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WW3onByw24osHME7kz2-jQo5JpX5KMhUgL.FoqESK57So2ceK22dJLoIp7LxKML1KBLBKnLxKqL1hnLBoMceo-7ehqpSo2p; WBPSESS=zVOFN-34dvyXIOdWJUJVmUZ1KpZqqsbJxzFqeD78OgYV50oXIp8DM3sBvSiJojLpSWcYQ1Rmt1vmzePaIco4AGlO67jNikwcCwPeNwVw77S8QrW4acx7SYc0Bl3i9yoetYjOONG2haNA1qQedKsyBQ=='''
# 定义工具输入
class GetUIDInput(BaseModel):
    query: str = Field(description="should be a search query")

class EmailInput(BaseModel):
    to: str = Field(description="Email address to send to. Example: email@example.com")
    sender: str = Field(
        description="Email address to send from. Example: email@example.com'"
    )
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body text")

class GetWeiboInfoInput(BaseModel):
    id: str = Field(description="should be a UID")

# 输入 "key1: value1, key2: value2"
def convert_string_to_dict(s):
    # 去除首尾的空格
    print("convert_string_to_dict", s)
    s = s.strip()

    # 去除开头和结尾的引号（如果有）
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]

    # 分割字符串，得到键值对列表
    pairs = [pair.strip() for pair in s.split(',')]

    # 构建字典
    result = {}
    for pair in pairs:
        key, value = pair.split(':', 1)
        key = key.strip().strip('"')
        value = value.strip().strip('"')
        result[key] = value
    print("convert_string_to_dict result", result)

    return result

# 输入如果是字符串类型的字典 则转化为字典类型
def convert_to_dict(s):
    try:
        if isinstance(s, str):
            d = ast.literal_eval(s)
            if isinstance(d, dict):
                return d
            else:
                d = convert_string_to_dict(s)
                if isinstance(d, dict):
                    return d
                else:
                    return None
                return None
        else:
            return None
    except (ValueError, SyntaxError):
        d = convert_string_to_dict(s)
        if isinstance(d, dict):
            return d
        else:
            return None

# @tool("获取微博UID", args_schema=GetUIDInput, return_direct=True)
def get_UID(query: str):
    """用于搜索获取网络页面数据"""
    search = CustomSerpAPIWrapper()
    search.serpapi_api_key = "63fadc9b8ef4dd06d1ef3daff72bfaeb114a3a4116b6e484058fb9a07476c7a2"
    res = search.run(f"{query}")
    print(f"get_UID!!! {res}")
    return extract_UID(res)

def extract_UID(urls: str):
    """提取 字符串数据 里面的 UID"""
    # string = "['https://weibo.com/u/2855071827', 'https://weibo.com/zz234?from=page_103505_profile&wvr=6&mod=like']"
    print("extract_url urls:", urls)
    pattern = r"\/u\/(\d+)"
    match = re.search(pattern, urls)
    if match:
        extracted_number = match.group(1)
        print("extract_url urls Success:", extracted_number)
        return extracted_number
    return None

def send_email(to: str, sender: str, subject: str, body: str):
    """用于发送邮件"""
    print(body, to, sender, subject)
    # 创建 SMTP 对象
    smtp = smtplib.SMTP()
    # 发件人邮箱地址
    sendAddress = sender
    # 发件人授权码
    password = 'kvugbrqjxnwwbbji'
    # 连接服务器
    server = smtplib.SMTP_SSL('smtp.qq.com', 465)

    # 登录邮箱
    loginResult = server.login(sendAddress, password)
    print(loginResult)

    # 构造MIMEText对象，参数为：正文，MIME的subtype，编码方式
    message = MIMEText(body, 'plain', 'utf-8')
    message['From'] = Header("me <{}>".format(sender))  # 发件人的昵称 用英文不报错
    message['To'] = Header("Anson <{}>".format(to))  # 收件人的昵称  用英文不报错
    message['Subject'] = Header(subject, 'utf-8')  # 定义主题内容
    print(message)
    server.sendmail(sender, to, message.as_string())

# @tool
def get_weiboInfo(id: str):
    """用于获取微博用户的详细资料"""
    print("用于获取微博用户的详细资料 id:", id)
    headers = {'User-Agent': "Apifox/1.0.0 (https://apifox.com)",
               'Referer': "https://weibo.com",
               'Accept': "application/json,text/plain,*/*",
               'Accept-Encoding': "gzip,deflate,br,zstd",
               'Accept-Language': "zh-CN",
               'X-Requested-With': "XMLHttpRequest",
               'X-Xsrf-Token': "rjRzy6SREVsdUIB1hXVoUcCa"
               }
    cookies = {
        "cookie": weibo_cookies,
    }
    url = "https://weibo.com/ajax/profile/detail?uid={}".format(id)
    print(url)
    response = requests.get(url, headers=headers, cookies=cookies, allow_redirects=False)
    text = bytes(response.text, 'utf-8').decode('unicode_escape')
    print(response.url, response.status_code, response.text, text, response.headers)
    html = json.loads(response.text)
    print(html)
    remove_non_chinese_fields(html)
    # html = "{'data': {'sunshine_credit': {'level': '信用极好'}, 'birthday': '1994-06-29 巨蟹座', 'description': '商务联系：yaochimudan@163.com（私信看不到） 想当一名专业演员的野生话剧演员', 'location': '四川 成都', 'real_name': {}, 'followers': {'users': [{'screen_name': '亚当flop亚当'}, {}, {'screen_name': '廖蹶子'}]}, 'label_desc': [{'name': '昨日互动数4', 'normal_mode': {}, 'dark_mode': {}}, {'name': '获赞赏次数277', 'normal_mode': {}, 'dark_mode': {}}, {'name': '视频累计播放量5.89亿', 'normal_mode': {}, 'dark_mode': {}}], 'desc_text': '微博原创视频博主', 'friend_info': '他有 <a>115</a> 个好友'}}"
    time.sleep(3)
    return html

def contains_chinese(s):
    return bool(re.search('[\u4e00-\u9fa5]', s))

# 移除非中文字段
def remove_non_chinese_fields(content):
    if isinstance(content, dict):
        to_remove = [key for key, value in content.items() if
                     isinstance(value, (str, int, float, bool)) and (not contains_chinese(str(value)))]
        for key in to_remove:
            del content[key]

        for key, value in content.items():
            if isinstance(value, (dict, list)):
                remove_non_chinese_fields(value)
    elif isinstance(content, list):
        to_remove_indices = []
        for i, item in enumerate(content):
            if isinstance(item, (str, int, float, bool)) and (not contains_chinese(str(item))):
                to_remove_indices.append(i)
            else:
                remove_non_chinese_fields(item)

        for index in reversed(to_remove_indices):
            content.pop(index)

def _handle_error(error: ToolException) -> str:
    return (
        "The following errors occurred during tool execution:"
        + error.args[0]
        + "Please try another tool."
    )