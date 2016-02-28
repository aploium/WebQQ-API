# -*- coding: utf-8 -*-
import webqq_api
from ColorfulPyPrint import *


def master_exec_python_code(qapi_obj, python_code, master_uin):
    """
    运行任意python代码并发送结果到master(注意安全)

    :type master_uin: int
    :type python_code: str
    :type qapi_obj: webqq_api.WebqqApi
    """
    from io import StringIO
    import sys

    _default_stdout = sys.stdout
    str_io = StringIO()
    try:
        sys.stdout = str_io
        exec(python_code)
        sys.stdout = _default_stdout
        qapi_obj.send_msg_slice(str_io.getvalue(), master_uin)
        infoprint(str_io.getvalue())  # 打印到正常的stdout
    except Exception as e:
        sys.stdout = _default_stdout
        qapi_obj.send_msg_slice('ERROR:' + str(e), master_uin)
        errprint('命令执行错误:', e)
    finally:
        sys.stdout = _default_stdout
        del str_io


def send_notice_to_qq(msg_content, target_qq, qapi_obj):
    """
    发送信息到对方qq

    :type target_qq: int
    :type msg_content: str
    :type qapi_obj: webqq_api.WebqqApi
    """

    infoprint('正在发送信息到qq', target_qq)
    return qapi_obj.send_msg_slice(msg_content, qapi_obj.q2u(target_qq))


def send_notice_to_discuss(msg_content, target_discuss_name, qapi_obj):
    """
    发送信息到讨论组

    :type target_discuss_name: str
    :type msg_content: str
    :type qapi_obj: webqq_api.WebqqApi
    """

    infoprint('正在发送信息到讨论组', target_discuss_name)
    return qapi_obj.send_msg_slice(msg_content, qapi_obj.discuss[target_discuss_name]['did'])
