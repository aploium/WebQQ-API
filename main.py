# -*- coding: utf-8 -*-
from time import sleep
from ColorfulPyPrint import *
from pprint import pprint
import pickle
import msg_handler
import os

try:
    from selenium import webdriver
    from requests import sessions, session, Response as reqResponse, get
    from requests.exceptions import ReadTimeout
except:
    errprint('需要selenium,requests包的支持,请安装: pip install selenium requests')
    exit()
import webqq_api
from server import msg_server_start

__VERSION__ = '1.09.00'
__author__ = 'aploium@aploium.com'


def print_usage_and_exit(error_code=0):
    global __VERSION__
    import sys
    from os.path import basename
    program_exec_cmd = 'python ' + basename(__file__)
    print('WebQQ消息服务器 Version: %s\n' % __VERSION__)
    print('请使用小号来登陆,因为webqq中自己不能发消息给自己')
    print('### 本程序需要系统已安装firefox ###')
    print('    -h --help: 显示本帮助')
    print('    -m (MasterQQ) --master-qq: [必须]指定大号QQ(不是登陆的QQ,登陆用账号需要是小号),'
          '当verbose=4时大号QQ有执行任意python命令的权限')
    print('    -d (masterDiscuss) --master-discuss: '
          '(可选)在webqq服务器出问题的这段时间(截止2016.03.07尚未恢复),指定接收信息的讨论组')
    print('    -v (0-4)  --verbose: verbose level 默认3')
    print('    -n  --new-session: 清理session并重新登陆(session被保存在脚本文件夹的session.dat中,有效期大约3天)')
    print()
    print('    -s  --start-server: 启动webqq消息服务器,供外部程序/计算机通过本机发送消息到qq(基本必用的一个选项,'
          '使用方法见同文件夹的webqq_client.py)')
    print('    -t (token) --token: '
          '(可选,建议指定)webqq消息服务器的token,其余程序/计算机必须给出正确的token才能发送消息,默认为 apl,'
          '使用多个-t指定多个可用token')
    print('    -p (port) --port: (可选,不建议修改)webqq消息服务器的端口,默认为34567')

    print()
    print(
        'example1: ' + program_exec_cmd + ' -m 333333333 -d "qwertyuiop" -s -v 4 -t "just_a_token" -t "another_token"')
    print('  在上例中,会打开firefox让你手动登陆(再次提醒,请登陆小号),大号qq为333333333,大号讨论组为qwertyuiop,启动webqq'
          '服务器,服务器token为just_a_token与another_token\n')
    sys.exit(error_code)


def parse_cmdline():
    import sys
    import getopt
    global masterQQ, masterDiscuss, verbose_level, force_new_session
    global is_start_msg_server, msg_server_tokens, msg_server_port
    required_args = {'-m'}  # 必须给定这些参数
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hnsm:d:v:t:p:",
                                   ['help', 'new-session', 'start-server', 'master-qq=', 'verbose=', 'master-discuss=',
                                    'token=', 'port='])
    except getopt.GetoptError as err:
        # print help information and exit:
        errprint(err)  # will print something like "option -a not recognized"
        print_usage_and_exit(1)

    for o, a in opts:
        if o in ("-h", "--help"):
            print_usage_and_exit(0)
        elif o in ("-m", "--master-qq"):
            masterQQ = int(a)  # 大号QQ
            if '-m' in required_args:
                required_args.remove('-m')  # 从必须参数中移除它,表示已经给出
        elif o in ("-d", "--master-discuss"):  # 讨论组
            masterDiscuss = a
        elif o in ("-v", "--verbose"):
            verbose_level = int(a)
        elif o in ("-n", "--new-session"):  # 重置session并从新登陆
            force_new_session = True
        elif o in ("-s", "--start-server"):  # 启动webqq消息服务器
            is_start_msg_server = True
        elif o in ("-t", "--token"):  # webqq消息服务器tokens
            msg_server_tokens.add(a)
        elif o in ("-p", "--port"):  # webqq消息服务器port
            msg_server_port = int(a)
        else:
            assert False, "给定了一个未知的参数: %s,请使用-h或者--help参数来查看帮助" % o
    if required_args:
        errprint('缺少以下参数:', *required_args)
        print_usage_and_exit(4)


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


infoprint('程序正在初始化,处理命令行参数')
os.chdir(os.path.dirname(__file__))  # 切换工作目录到脚本所在文件夹
force_new_session = False
is_start_msg_server = False
msg_server_tokens = set()
msg_server_port = None
verbose_level = 3
masterQQ = 358890739
masterDiscuss = ''
session_file = r'session.dat'
is_proxy = False  # 所有请求的代理,在程序开发时手动修改
proxy = {  # 仅在is_proxy==True时生效
    "http": "http://127.0.0.1:8882",
    "https": "http://127.0.0.1:8882",
}
infoprint('处理命令行参数')
parse_cmdline()  # 解析命令行参数
if is_start_msg_server and not msg_server_tokens:  # 若没有指定token则使用默认值
    warnprint('没有指定token,将使用默认值apl,这可能会带来安全问题,请使用 -t 参数来自定义token')
    msg_server_tokens = {'apl'}
if force_new_session:
    infoprint('将重置session并重新登陆,session文件为程序同目录的session.dat')
apoutput_set_verbose_level(verbose_level)
# #######################################
clients_dic = {}
is_new_session = True
if not force_new_session:  # 若未指定重置session则尝试读取session文件
    try:
        # 尝试读取session文件
        qapi = webqq_api.load_session(session_file)
        assert isinstance(qapi, webqq_api.WebqqApi)
        infoprint('Session文件读取成功,session版本:', qapi.api_version,
                  '创建时间:', qapi.when_was_i_born())
        is_new_session = False  # 若读取成功则跳过下面的初始化
    except:
        # 若读取失败则初始化
        infoprint('Session文件不存在,将初始化')

if is_new_session or force_new_session:
    qapi = webqq_api.WebqqApi(verbose_level=verbose_level)
    # 重新走一遍登陆流程
    infoprint('正在打开firefox')
    importantprint('接下来用户只需要扫码登陆小号,此后不需要任何用户操作\n'
                   '注:程序会跳转到其他网站(如www.qq.com)来获取cookies')
    driver = selenium_driver_init()  # 初始化selenium
    driver.get('http://w.qq.com/')  # webqq首页
    importantprint('请在打开的firefox中手动登陆webQQ')
    while True:  # 等待登陆
        temp = driver.find_elements_by_id('contact')
        if temp:
            break
        else:
            sleep(1)

    infoprint('登陆完成,等待5秒后程序自动从浏览器提取信息')
    sleep(5)
    infoprint('正在获取cookies,此阶段会跳转到web.qq.com、www.qq.com等网站,这是正常步骤')
    qapi.fetch_cookies_from_selenium(driver)
    infoprint('正在获取一些参数')
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
    qapi.fetch_friends_dict_from_page_source(driver.page_source)  # 保存页面源码备用
    qapi.master_qq = masterQQ  # 设置主人QQ
    if masterDiscuss:
        qapi.master_discuss_name = masterDiscuss  # 设置主人讨论组
    infoprint('数据获取完成,正在关闭浏览器')
    driver.quit()  # 关闭浏览器
    infoprint('初始化完成,将数据写入session.dat备用')
    with open(session_file, 'wb') as fp:
        pickle.dump(qapi, fp)

assert isinstance(qapi, webqq_api.WebqqApi)

qapi.proxies = proxy if is_proxy else {}
masterUin = qapi.q2u(qapi.master_qq)  # 根据主人的qq获取uin,对uin的具体说明见webqq_api.py中WebqqApi类的顶部
dbgprint('登陆账号的QQ联系人/群/讨论组:', qapi.qq_to_uin_dict)
# 发送启动信息
infoprint('正在发送启动信息')
# 发送启动信息到主人的qq
qapi.send_msg_slice('WebQQ system ONLINE version: ' + __VERSION__, qapi.q2u(qapi.master_qq))
if masterDiscuss:
    qapi.send_msg_slice('WebQQ system ONLINE version: ' + __VERSION__, qapi.discuss[qapi.master_discuss_name]['did'])

# 初始化服务器,这是本程序的主要功能
#     消息服务器会新开一个线程来监听其余程序/计算机的消息请求
#     请求接口/格式见webqq_client.py
if is_start_msg_server:
    infoprint('正在启动webqq消息服务器')
    msg_server_start(qapi, tokens=msg_server_tokens, listen_port=msg_server_port)

# 接受信息,这里没什么用,只是用来debug
infoprint('开始接收信息')
while True:
    try:
        msg = qapi.pull_message()  # 从服务器读取信息,若没有新信息则会阻塞到超时,超时后from_uin会被设置成0
        pprint(msg)
        sender_uin = msg['from_uin']
        msg_content = msg['content']
        if verbose_level >= 4 and sender_uin != masterUin and sender_uin != 0:
            qapi.send_message('RECEIVED MSG from' + str(qapi.u2q(sender_uin)) + ': \n' + msg_content, masterUin)

        # 在debug模式(verbose=4)中,赋予masterQQ执行任意python代码的权限
        #     执行格式为大号向小号发送exec some_python_code
        #     如:exec print("hello world")
        #     所有print的显示都会以QQ消息的形式被返回给大号
        if verbose_level >= 4 and sender_uin == masterUin \
                and msg_content[:5] == 'exec ':
            msg_handler.master_exec_python_code(qapi, msg_content[5:], masterQQ)

    except Exception as e:
        errprint('监听信息时发生错误:', e)
        sleep(5)
