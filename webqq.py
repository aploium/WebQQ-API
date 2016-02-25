# -*- coding: utf-8 -*-
from time import sleep, time
from ColorfulPyPrint import *
from pprint import pprint
import pickle
import sys
from io import StringIO

try:
    from selenium import webdriver
    from requests import sessions, session, Response as reqResponse, get
    from requests.exceptions import ReadTimeout
except:
    errprint('需要selenium,requests包的支持,请安装: pip install selenium requests')
    exit()
import webqq_api

__VERSION__ = '1.01.02'
WEBQQ_MSG_SIZE_LIMIT = 900


def print_usage_and_exit():
    print('usage')
    exit()


def selenium_driver_init():
    infoprint('正在初始化浏览器')
    try:
        _driver = webdriver.Firefox()
    except Exception as exp:
        errprint('初始化失败. 请检查是否已安装最新版firefox,错误信息:', exp)
        print_usage_and_exit()
    else:
        return _driver
    return None


verbose_level = 4
apoutput_set_verbose_level(verbose_level)
masterQQ = 358890739
session_file = r'session.dat'
clients_dic = {}
DEBUG_PROXY = {
    "http": "http://127.0.0.1:8882",
    "https": "http://127.0.0.1:8882",
} if False else {}
is_new_session = True
try:
    # 尝试读取session文件
    qapi = webqq_api.load_session(session_file)
    assert isinstance(qapi, webqq_api.WebqqApi)
    infoprint('Session文件读取成功,session版本:', qapi.api_version,
              '创建时间:', qapi.when_was_i_born())
    is_new_session = False
except:
    # 若读取失败则初始化
    infoprint('Session文件不存在,正在初始化')
    qapi = webqq_api.WebqqApi(verbose_level=verbose_level)

if is_new_session:
    # 重新走一遍登陆流程
    infoprint('正在打开firefox')
    driver = selenium_driver_init()
    driver.get('http://w.qq.com/')
    importantprint('请在打开的firefox中登陆webQQ')
    while True:  # 等待登陆
        temp = driver.find_elements_by_id('contact')
        if temp:
            break
        else:
            sleep(1)

    infoprint('登陆完成,等待5秒后从浏览器提取信息')
    sleep(5)
    infoprint('正在获取cookies')
    qapi.fetch_cookies_from_selenium(driver)
    infoprint('获取一些参数')
    qapi.lazy_init()
    while True:  # 等待载入到可以获取用户列表为止
        temp = driver.find_elements_by_id('groupBodyUl-0')
        if temp:
            infoprint('成功载入页面源码')
            sleep(3)
            break
        else:
            sleep(3)
    infoprint('获取用户列表')
    qapi.fetch_friends_dict_from_page_source(driver.page_source)
    driver.quit()
    infoprint('初始化完成,将数据写入session备用')
    with open(session_file, 'wb') as fp:
        pickle.dump(qapi, fp)

assert isinstance(qapi, webqq_api.WebqqApi)

qapi.proxies = DEBUG_PROXY
masterUin = qapi.q2u(masterQQ)
# 发送启动信息
infoprint('正在发送启动信息')
qapi.send_message('WebQQ system ONLINE', qapi.q2u(masterQQ))

# 接受信息
while True:
    msg = qapi.pull_message()
    pprint(msg)
    sender_uin = msg['from_uin']
    msg_content = msg['content']
    try:
        qapi.send_message('RECEIVED MSG: ' + msg_content, sender_uin)
    except Exception as e:
        qapi.send_message('发送失败:' + str(e), sender_uin)
    if verbose_level >= 4 and sender_uin != masterUin and sender_uin != 0:
        qapi.send_message('RECEIVED MSG from' + str(qapi.u2q(sender_uin)) + ': \n' + msg_content, masterUin)

    # 在测试模式中,赋予master执行任意命令的权限
    if verbose_level >= 4 and sender_uin == masterUin:
        if msg_content[:5] == 'exec ':
            _default_stdout = sys.stdout
            str_io = StringIO()
            try:
                sys.stdout = str_io
                exec(msg_content[5:])
                sys.stdout = _default_stdout
                str_io.seek(0)
                buffer = str_io.readline(WEBQQ_MSG_SIZE_LIMIT)
                while buffer:
                    result = qapi.send_message(buffer, masterUin)
                    buffer = str_io.readline(WEBQQ_MSG_SIZE_LIMIT)
                print(str_io.getvalue())  # 打印到正常的stdout
            except Exception as e:
                sys.stdout = _default_stdout
                qapi.send_message('ERROR:' + str(e), masterUin)
                errprint('命令执行错误:', e)
            finally:
                sys.stdout = _default_stdout
                del str_io
