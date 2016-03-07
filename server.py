# -*- coding: utf-8 -*-
"""
webqq消息服务器,供外部程序/计算机通过本机发送消息到qq
外部程序的请求格式见webqq_client.py中的说明
"""
import socket
import threading
from urllib.parse import unquote_plus
from re import findall as re_findall, MULTILINE as RE_MULTILINE, DOTALL as RE_DOTALL
from ColorfulPyPrint import *
import msg_handler
from time import time

__author__ = 'aploium@aploium.com'
DEFAULT_PORT = 34567


# #########  stand along functions  #############

def extract_paras(string):
    """
    从用户的请求中解析出参数,具体格式见webqq_client.py中的说明
    :param string: str
    """
    search = re_findall(r'_(?P<name>\w+?)_=_\{\{\{\{(?P<value>.*?)\}\}\}\}_', string, flags=RE_MULTILINE | RE_DOTALL)
    return {name: value for name, value in search}


def handle_tcp_request(sock, addr, webqq_obj, tokens):
    """
    处理传入的tcp连接
    """
    buffer_size = 1024
    buffer = []
    while True:  # 接受对方所有的输入内容
        d = sock.recv(buffer_size)
        infoprint(len(d), d)
        buffer.append(d)
        if len(d) < buffer_size:
            break
    data = b''.join(buffer)
    try:  # 对于windows cmd的直接发送,数据是gbk编码的,需要尝试解码
        data = data.decode(encoding='utf-8')
        dbgprint('charset=utf-8')
    except:
        data = data.decode(encoding='gbk')
        dbgprint('charset=gbk')
    data = unquote_plus(data)  # urldecode
    paras = extract_paras(data)  # 根据格式提取出有效参数

    dbgprint(*addr, 'request paras:', paras)

    # 需要cmd参数
    if 'cmd' not in paras:
        warnprint('缺少cmd参数,链接关闭')
        sock.send(b'cmd missing  ' + str(time()).encode())
        sock.close()
        return

    # 验证token
    if tokens is not None and \
            ('token' not in paras or paras['token'] not in tokens):
        warnprint('token缺失或错误,链接关闭')
        sock.send(b'token missing or wrong  ' + str(time()).encode())
        sock.close()
        return

    # 处理命令
    if paras['cmd'] == 'sendtodis':  # 发送到讨论组
        msg_handler.send_notice_to_discuss(paras['msg'], paras['target'], webqq_obj)
    elif paras['cmd'] == 'sendtoqq':  # 发送到qq私聊
        msg_handler.send_notice_to_qq(paras['msg'], int(paras['target']), webqq_obj)
    elif paras['cmd'] == 'handshake':  # 握手
        sock.send(b'handshakeOK')

    sock.send(b'thank you')
    sock.close()


def tcp_listen(port, webqq_obj, tokens):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', port))  # 监听0.0.0.0表示允许任意客户端ip
    s.listen(50)  # 最大允许客户端数
    while True:
        try:
            sock, addr = s.accept()  # 接受一个传入TCP连接
            infoprint('accept connection from', addr)
            t = threading.Thread(target=handle_tcp_request,
                                 args=(sock, addr, webqq_obj, tokens)
                                 )  # 新线程处理这个传入连接
            t.start()
        except Exception as e:
            errprint('在处理webqq客户端信息时发生错误:', e)


def msg_server_start(webqq_obj, tokens=None, listen_port=None):
    if tokens is None:
        warnprint('没有指定token,可能导致恶意利用')
    if listen_port is None:
        listen_port = DEFAULT_PORT
    dbgprint('tokens=', tokens)
    infoprint('Listening LPort: %d' % listen_port)
    # 创建一个监听用线程
    t = threading.Thread(target=tcp_listen, args=(listen_port, webqq_obj, tokens))
    t.start()
