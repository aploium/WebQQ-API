import socket
import threading
from urllib.parse import unquote_plus
import subprocess
from re import findall as re_findall
from ColorfulPyPrint import *
import msg_handler
from time import time

DEFAULT_PORT = 34567


# #########  stand along functions  #############

def generate_tcp_port_blacklist(tcp_port_blacklist=None):
    if tcp_port_blacklist is None:
        tcp_port_blacklist = set()
    cmd = 'netstat -an'
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output = p.communicate()[0].decode('gbk')

    # ###### TCP ######
    match = re_findall(r' +TCP +\d+\.\d+\.\d+\.\d+:(?P<lport>\d+)'
                       r' +\d+\.\d+\.\d+\.\d+:\d+'
                       r' +\w+ *', output)
    for port in match:
        tcp_port_blacklist.add(int(port))
    return tcp_port_blacklist


def extract_paras(string):
    search = re_findall(r'_(?P<name>\w+?)_=_\{\{\{\{(?P<value>.*?)\}\}\}\}_', string)
    return {name: value for name, value in search}


def handle_tcp_request(sock, addr, webqq_obj, tokens):
    buffer_size = 1024
    buffer = []
    while True:
        d = sock.recv(buffer_size)
        infoprint(len(d), d)
        buffer.append(d)
        if len(d) < buffer_size:
            break
    data = b''.join(buffer)
    try:
        data = data.decode(encoding='utf-8')
        dbgprint('charset=utf-8')
    except:
        data = data.decode(encoding='gbk')
        dbgprint('charset=gbk')
    data = unquote_plus(data)
    paras = extract_paras(data)

    dbgprint(*addr, 'request paras:', paras)

    # 需要cmd参数
    if 'cmd' not in paras:
        warnprint('缺少cmd参数')
        sock.send(b'cmd missing  ' + str(time()).encode())
        sock.close()
        return

    # 验证token
    if tokens is not None and \
            ('token' not in paras or paras['token'] not in tokens):
        warnprint('token缺失或错误')
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
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', port))
        s.listen(4)
        sock, addr = s.accept()
        infoprint('accept connection from', addr)
        t = threading.Thread(target=handle_tcp_request, args=(sock, addr, webqq_obj, tokens))
        t.start()


def msg_server_start(webqq_obj, tokens=None, listen_port=DEFAULT_PORT):
    if tokens is None:
        warnprint('没有指定token,可能导致恶意利用')
    dbgprint('tokens=', tokens)
    tcp_port_black_list = generate_tcp_port_blacklist()
    while listen_port in tcp_port_black_list:
        listen_port += 1
    infoprint('Listening LPort: %d' % listen_port)
    t = threading.Thread(target=tcp_listen, args=(listen_port, webqq_obj, tokens))
    t.start()


if __name__ == '__main__':
    apoutput_set_verbose_level(3)
    port = 80
    tcpPortBlackList = generate_tcp_port_blacklist()
    while port in tcpPortBlackList:
        port += 1
    infoprint('Listening LPort: %d' % port)
    tcp_listen(port)
