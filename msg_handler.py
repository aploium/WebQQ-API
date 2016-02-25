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
