# -*- coding: utf-8 -*-
"""
一堆API(非官方,在开发过程中自己测试出来的)
"""
from json import loads as json_loads, dumps as json_dumps
from time import sleep, time, strftime, localtime
from urllib.parse import quote_plus
from html.parser import HTMLParser
import pickle
from ColorfulPyPrint import *
from random import randint

try:
    from selenium import webdriver
    from requests import sessions, session as requests_init_session, Response as reqResponse, get
    from requests.exceptions import ReadTimeout
except:
    errprint('需要selenium,requests包的支持,请安装: pip install selenium requests')
    exit()
from cookies_convert import selenium2requests

__VERSION__ = '1.09.00'
API_VERSION = '1.09.00'

DEFAULT_WEBQQ_CLIENTID = 53999199
WEBQQ_MSG_SIZE_LIMIT = 850
MSG_SEND_DELAY = 0.2  # seconds


def html_unescape(string):
    """
    简陋的html特殊字符反转义

    :type string: str
    """
    return str(string).replace('&gt;', '>').replace('&lt;', '<')


def load_session(session_file):
    """
    更新session版本

    :type session_file: str
    """
    with open(session_file, 'rb') as fp:
        old_api = pickle.load(fp)
    assert isinstance(old_api, WebqqApi)

    if old_api.api_version < API_VERSION:  # 更新API版本
        new_api = WebqqApi(**(old_api.get_all_variable()))
        new_api.lazy_init()
        new_api.fetch_friends_dict_from_page_source(new_api.page_source)
        with open(session_file, 'wb') as fp:
            pickle.dump(new_api, fp)  # 更新session文件中的版本
        return new_api
    else:
        return old_api


def extract_uin_from_page_source(page_source):
    """
    用内置库从页面源码提取出uin

    :type page_source: str
    """

    class MyHTMLParser(HTMLParser):
        def set_var(self):
            self.var = {'discuss': set(),
                        'friend': set(),
                        'group': set()}

        def handle_starttag(self, tag, attrs):
            for attr in attrs:
                if attr[0] == '_type':
                    uin_type = attr[1]
                    for attrb in attrs:
                        if attrb[0] == '_uin':
                            self.var[uin_type].add(int(attrb[1]))

    parser = MyHTMLParser()
    parser.set_var()
    parser.feed(page_source)
    return parser.var


class WebqqApi(object):
    """
    一套封装为python类的webqq的API

    对uin的说明:
      腾讯后台对用户的标记并不是以QQ为标示的,而是以一串uin的数字(qq/群/讨论组都有uin).
    讨论组和qq群的uin是固定不变的,而QQ用户的uin会发生改变(改变方式暂不清楚)
      在发送/接受信息时,腾讯服务器接受/给出的都是uin而不是QQ号/群号
    """

    def update_headers(self, headers=None):
        """
        设置headers
        :type headers: dict

        """
        if headers is None:
            self.requests_sess.headers.update(
                {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:45.0) Gecko/20100101 Firefox/45.0",
                 "Referer": "http://d1.web2.qq.com/proxy.html?v=20151105001&callback=1&id=2",
                 "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3"})
        else:
            self.requests_sess.headers.update(**headers)

    def _send_get(self, url, data_dict, **extra_request_kw):
        try:
            response = self.requests_sess.get(url, params=data_dict, **extra_request_kw)
        except Exception as e:
            errprint('GET请求发送错误,原因:', e)
            raise
        try:  # 解析返回的json
            rsp_json = json_loads(response.text)
        except Exception as e:
            errprint('无法解析返回的json,错误信息', e)
            dbgprint('返回值:', response.text)
            raise
        else:
            return rsp_json

    def _send_post(self, url, data_enc, headers, **extra_request_kw):
        try:
            response = self.requests_sess.post(url, data=data_enc, headers=headers, **extra_request_kw)
        except Exception as e:
            errprint('POST请求发送错误,原因:', e)
            raise
        try:  # 解析返回的json
            rsp_json = json_loads(response.text)
        except Exception as e:
            errprint('无法解析返回的json,错误信息', e)
            dbgprint('返回值:', response.text)
            raise
        else:
            return rsp_json

    def _request_and_parse(self, method, url, data_dict, **extra_request_kw):
        """
        发送API请求到服务器,接受并解析响应.内置基本的重试
        :type data_dic: dict
        :type url: str
        :type method: str

        """

        # 设置proxies,避免覆盖
        if 'proxies' not in extra_request_kw:
            extra_request_kw['proxies'] = self.proxies

        if method == 'GET':
            for i in range(self.max_retries_count):
                if i:  # 重试前的延迟
                    infoprint(self.retries_delay, '秒后进行第', i, '次重试')
                    sleep(self.retries_delay)
                    # 若重试全部失败则会运行到函数尾部
                try:
                    rsp_json = self._send_get(url, data_dict, **extra_request_kw)
                except Exception as e:  # 进行重试
                    errprint('API请求失败,错误原因:', e)
                    dbgprint('请求参数')
                    continue
                else:  # 请求成功
                    return rsp_json

        elif method == 'POST':
            try:  # 转码数据json
                data_enc = 'r=' + quote_plus(json_dumps(data_dict))
            except Exception as e:
                errprint('试图转换请求为json时发生错误:', e)
                raise
                # 需要手动添加Content-Type头
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            # 防止用户定义的headers冲突
            if 'headers' in extra_request_kw:
                headers.update(extra_request_kw.pop('headers'))
            for i in range(self.max_retries_count):
                if i:  # 重试前的延迟
                    infoprint(self.retries_delay, '秒后进行第', i, '次重试')
                    sleep(self.retries_delay)
                    # 若重试全部失败则会运行到函数尾部
                try:
                    rsp_json = self._send_post(url, data_enc, headers, **extra_request_kw)
                except Exception as e:  # 进行重试
                    errprint('API请求失败,错误原因:', e)
                    continue
                else:  # 请求成功
                    return rsp_json

        else:  # 若参数正常则不应该执行到这里
            raise ValueError('指定了错误的参数')

        # 仅当重试失败时才会执行到此,抛出异常
        dbgprint('达到最大失败次数,请求参数:',
                 '\nmethod:', method,
                 '\nurl:', url,
                 '\ndata:', data_dict,
                 '\nextra_kw:', extra_request_kw)
        raise BaseException('达到最大失败次数')

    def get_psessionid(self, ptwebqq="", clientid=0):
        """
        获取psessionid

        :type clientid: int
        :type ptwebqq: str
        """

        rsp_json = self._request_and_parse(
            method='POST',
            url='http://d1.web2.qq.com/channel/login2',
            data_dict={
                "ptwebqq": ptwebqq if ptwebqq else self.ptwebqq,
                "clientid": clientid if clientid else self.clientid,
                "psessionid": "",
                "status": "online"
            }
        )
        dbgprint('获取psessionid', rsp_json, v=4)
        return rsp_json['result']['psessionid']

    def get_vfwebqq(self, ptwebqq="", psessionid="", clientid=0):
        """
        获取vfwebqq

        :type psessionid: str
        :type clientid: int
        :type ptwebqq: str
        """
        rsp_json = self._request_and_parse(
            method='GET',
            url='http://s.web2.qq.com/api/getvfwebqq',
            data_dict={
                'ptwebqq': ptwebqq if ptwebqq else self.ptwebqq,
                'clientid': clientid if clientid else self.clientid,
                'psessionid': psessionid if psessionid else self.psessionid,
                't': int(time())
            }
        )

        dbgprint('获取vfwebqq', rsp_json, v=4)
        return rsp_json['result']['vfwebqq']

    def get_info_from_uin(self, uin, vfwebqq="", psessionid="", clientid=0):
        """
        获取详细的个人信息

        :type psessionid: str
        :type clientid: int
        :type vfwebqq: str
        :type uin: int

        return example:
        {   'allow': 1,
            'birthday': {'day': 16, 'month': 8, 'year': 1995},
            'blood': 3,
            'city': '杭州',
            'client_type': 1,
            'college': '浙江大学',
            'constel': 7,
            'country': '中国',
            'email': 'aploium@aploium.com',
            'face': 0,
            'gender': 'male',
            'homepage': 'aploium.com',
            'mobile': '189********',
            'nick': 'Aploium',
            'occupation': '小学',
            'personal': '冗余的RAID0，不丢包的UDP，没缩进的Python，HTML5满分的IE6，循环的π，忘记你的我与想我的你',
            'phone': '1786543210',
            'province': '浙江',
            'shengxiao': 12,
            'stat': 10,
            'uin': 1084780654,
            'vip_info': 5
        }
        """

        rsp_json = self._request_and_parse(
            method='GET',
            url='http://s.web2.qq.com/api/get_friend_info2',
            data_dict={
                'tuin': uin,
                'vfwebqq': vfwebqq if vfwebqq else self.vfwebqq,
                'clientid': clientid if clientid else self.clientid,
                'psessionid': psessionid if psessionid else self.psessionid,
                't': int(time())  # unix time
            }
        )

        dbgprint('获取个人信息', rsp_json)
        return rsp_json['result']

    def get_qq_from_uin(self, uin, target_type=1, vfwebqq=""):
        """
        根据uin获取QQ号

        :type target_type: int
        :type vfwebqq: str
        :type uin: int
        """

        rsp_json = self._request_and_parse(
            method='GET',
            url='http://s.web2.qq.com/api/get_friend_uin2',
            data_dict={
                'tuin': uin,
                'vfwebqq': vfwebqq if vfwebqq else self.vfwebqq,
                't': int(time()),  # unix time
                'type': target_type
            }
        )

        dbgprint('获取QQ号', rsp_json, v=4)
        return rsp_json['result']['account']

    def get_user_signature_from_uin(self, uin, vfwebqq=""):
        """
        获取个性签名

        :type vfwebqq: str
        :type uin: int
        """

        rsp_json = self._request_and_parse(
            method='GET',
            url='http://s.web2.qq.com/api/get_single_long_nick2',
            data_dict={
                'tuin': uin,
                'vfwebqq': vfwebqq if vfwebqq else self.vfwebqq,
                't': int(time()),  # unix time
            }
        )
        dbgprint('获取个性签名', rsp_json, v=4)
        return rsp_json['result'][0]['lnick']

    def get_recent_contact_list(self, vfwebqq="", psessionid="", clientid=0):
        """
        获取最近联系人列表

        :type clientid: int
        :type vfwebqq: str
        :type psessionid: str
        """

        rsp_json = self._request_and_parse(
            method='POST',
            url='http://d1.web2.qq.com/channel/get_recent_list2',
            data_dict={
                "vfwebqq": vfwebqq if vfwebqq else self.vfwebqq,
                "clientid": clientid if clientid else self.clientid,
                "psessionid": psessionid if psessionid else self.psessionid
            }
        )

        if 'result' in rsp_json:  # 成功收到信息
            return rsp_json['result']
        else:
            errprint('在接受信息时发生错误:', rsp_json)
            return False  # 其他错误

    def send_message(self, msg_content, target_uin, psessionid="", face=525, msg_id=42120002,
                     clientid=0):
        """
        向目标(uin)发送信息,建议用自带分片的send_msg_slice代替

        :type clientid: int
        :type msg_id: int
        :type face: int
        :type target_uin: int
        :type psessionid: str
        :type msg_content: str
        """
        rsp_json = self._request_and_parse(
            method='POST',
            url='http://d1.web2.qq.com/channel/send_buddy_msg2',
            data_dict={
                'clientid': clientid if clientid else self.clientid,
                'content': json_dumps(  # 蛋疼的content需要预dump一次
                    [
                        msg_content,  # 信息内容主体
                        ["font", {"name": "宋体",
                                  "size": 10,
                                  "style": [0, 0, 0],
                                  "color": "000000"}
                         ]
                    ]
                ),
                'face': face,
                'msg_id': msg_id + randint(0, 12120002),
                'psessionid': psessionid if psessionid else self.psessionid,
                'to': target_uin  # 接收对象
            }
        )

        if 'errCode' in rsp_json and rsp_json['errCode'] == 0 or rsp_json['retcode'] == 1202:
            return True
        else:
            errprint('发送信息失败:', rsp_json)
            return False

    def send_msg_slice(self, msg_content, target_uin, **kwargs):
        """
        将长消息分片发送(短消息也建议用这个函数)

        :type target_uin: int
        :type msg_content: str
        """
        msg_type = self.uin_type[target_uin]
        send_function = {'friend': self.send_message, 'discuss': self.send_discuss_msg}[msg_type]
        if len(msg_content) <= WEBQQ_MSG_SIZE_LIMIT:  # 长度足够小,正常发送
            return send_function(msg_content, target_uin, **kwargs)

        slices_num = (len(msg_content) + WEBQQ_MSG_SIZE_LIMIT // 2) // WEBQQ_MSG_SIZE_LIMIT
        for i in range(slices_num - 1):
            send_function('[[' + str(i + 1) + '/' + str(slices_num) + ']]'
                          + msg_content[i * WEBQQ_MSG_SIZE_LIMIT:(i + 1) * WEBQQ_MSG_SIZE_LIMIT], target_uin,
                          **kwargs)
            sleep(MSG_SEND_DELAY)
        return send_function('[[' + str(slices_num) + '/' + str(slices_num) + ']]'
                             + msg_content[(slices_num - 1) * WEBQQ_MSG_SIZE_LIMIT:], target_uin, **kwargs)

    def send_discuss_msg(self, msg_content, target_did, clientid=0, psessionid="", face=525, msg_id=72690003):
        """
        发送信息到讨论组
        """
        rsp_json = self._request_and_parse(
            method='POST',
            url='http://d1.web2.qq.com/channel/send_discu_msg2',
            data_dict={
                'clientid': clientid if clientid else self.clientid,
                'content': json_dumps(  # 蛋疼的content需要预dump一次
                    [
                        msg_content,  # 信息内容主体
                        ["font", {"name": "宋体",
                                  "size": 10,
                                  "style": [0, 0, 0],
                                  "color": "000000"}
                         ]
                    ]
                ),
                'face': face,
                'msg_id': msg_id + randint(0, 12120002),
                'psessionid': psessionid if psessionid else self.psessionid,
                'did': target_did  # 接收对象
            }
        )

        if 'errCode' in rsp_json and rsp_json['errCode'] == 0 or rsp_json['retcode'] == 1202:
            return True
        else:
            errprint('发送信息失败:', rsp_json)
            return False

    def pull_message(self, ptwebqq="", psessionid="", clientid=0, key='', timeout=0):
        """
        接受信息
        返回值参考:
        {
            'content': 'some message',
            'from_uin': 1084780654,
            'msg_id': 1906,
            'msg_type': 0,
            'time': 1456124657,
            'to_uin': 2153227440
        }

        :type timeout: int
        :type key: str
        :type clientid: int
        :type ptwebqq: str
        :type psessionid: str
        """
        try:
            rsp_json = self._request_and_parse(
                method='POST',
                url='http://d1.web2.qq.com/channel/poll2',
                data_dict={
                    "ptwebqq": ptwebqq if ptwebqq else self.ptwebqq,
                    "clientid": clientid if clientid else self.clientid,
                    "psessionid": psessionid if psessionid else self.psessionid,
                    "key": key
                },
                timeout=timeout if timeout else self.pull_msg_timeout
            )
        except:
            return {'from_uin': 0, 'content': ''}  # 没收到信息
        else:
            if 'result' in rsp_json:  # 成功收到信息
                rsp_json = rsp_json['result'][0]['value']
                # 服务器返回的信息内容是html转义的,需要还原回来
                rsp_json['content'] = html_unescape(rsp_json['content'][-1])
                return rsp_json
            elif 'retcode' in rsp_json and rsp_json['retcode'] == 0:
                return {'from_uin': 0, 'content': ''}  # 没收到信息
            else:
                errprint('在接受信息时发生错误:', rsp_json)
                return False  # 其他错误

    def fetch_cookies_from_selenium(self, driver):
        """
        从selenium中获取webqq的cookies供requests用(这个函数健壮性很差)
        """
        self.requests_sess.cookies = selenium2requests(driver.get_cookies(), self.requests_sess.cookies)
        driver.get('http://web.qq.com/')
        sleep(3)
        self.requests_sess.cookies = selenium2requests(driver.get_cookies(), self.requests_sess.cookies)
        driver.get('http://web2.qq.com/')
        sleep(3)
        self.requests_sess.cookies = selenium2requests(driver.get_cookies(), self.requests_sess.cookies)
        driver.get('http://l.qq.com/')
        sleep(3)
        self.requests_sess.cookies = selenium2requests(driver.get_cookies(), self.requests_sess.cookies)
        driver.get('http://qq.com/')
        sleep(3)
        self.requests_sess.cookies = selenium2requests(driver.get_cookies(), self.requests_sess.cookies)
        driver.get('http://w.qq.com/')

    def get_discuss_info(self, did, vfwebqq="", clientid=0, psessionid=""):
        """
        获取讨论组信息
        :type psessionid: str
        :type clientid: int
        :param did: int
        """

        rsp_json = self._request_and_parse(
            method='GET',
            url='http://d1.web2.qq.com/channel/get_discu_info',
            data_dict={
                'did': did,
                'vfwebqq': vfwebqq if vfwebqq else self.vfwebqq,
                'clientid': clientid if clientid else self.clientid,
                'psessionid': psessionid if psessionid else self.psessionid,
                't': int(time()),  # unix time
            }
        )
        dbgprint('获取群信息', rsp_json, v=4)
        return rsp_json['result']['info']

    def fetch_friends_dict_from_page_source(self, page_source):
        """
        从页面源码中提取出好友uin列表,并转化为QQ号-uin的字典

        :type page_source: str
        """
        self.page_source = page_source
        uin_list = extract_uin_from_page_source(page_source)
        for uin in uin_list['friend']:  # 好友列表
            qq = int(self.get_qq_from_uin(uin))
            self.qq_to_uin_dict[qq] = uin
            self.uin_to_qq_dict[uin] = qq
            self.uin_type[uin] = 'friend'

        for did in uin_list['discuss']:  # 好友列表
            discuss_info = self.get_discuss_info(did)
            self.discuss[discuss_info['discu_name']] = discuss_info
            self.uin_type[did] = 'discuss'

            # for uin in uin_list['group']:  # 群列表
            #     qq = int(self.get_qq_from_uin(uin))
            #     self.qq_to_uin_dict[qq] = uin
            #     self.uin_to_qq_dict[uin] = qq

    def lazy_init(self):
        """
        自动获取一些参数
        """
        self.ptwebqq = self.requests_sess.cookies.get_dict('.qq.com')['ptwebqq']
        self.psessionid = self.get_psessionid()
        self.vfwebqq = self.get_vfwebqq()

    def when_was_i_born(self):
        """
        返回这个session被创建的时间(人类可阅读)
        """
        return strftime("%Y-%m-%d %H:%M:%S", localtime(self.create_time))  # 这个session被创建的时间

    def change_verbose_level(self, verbose_level=1):
        """
        更改verbose level,留空则重置为默认
        :type verbose_level: int
        """
        self.verbose_level = verbose_level
        apoutput_set_verbose_level(verbose_level)

    def q2u(self, qq):
        """
        一个缩写的qq到uin转换函数

        :type qq: int
        """
        if qq in self.qq_to_uin_dict:
            return self.qq_to_uin_dict[qq]
        else:
            return None

    def u2q(self, uin):
        """
        一个缩写的uin到qq转换函数

        :type uin: int
        """
        if uin in self.uin_to_qq_dict:
            return self.uin_to_qq_dict[uin]
        else:
            return None

    def get_all_variable(self):
        """
        取出类中所有变量
        """
        var = {}
        for v in dir(self):
            if not isinstance(type(self.__getattribute__(v)), type(self.get_all_variable)) \
                    and '__' not in v:
                var[v] = self.__getattribute__(v)
        return var

    def __init__(self, master_qq=0, master_discuss_name=None, requests_sess=None, proxies=None, create_time=0,
                 qq_to_uin_dict=None, uin_to_qq_dict=None, page_source=None,
                 verbose_level=1, pull_msg_timeout=200,
                 max_retries_count=5, retries_delay=5, clientid=0, **kwargs):
        """
        :type clientid: int
        :type retries_delay: float
        :type max_retries_count: int
        :type verbose_level: int
        :type requests_sess: sessions.Session
        """
        self.api_version = API_VERSION
        self.ptwebqq = ""
        self.psessionid = ""
        self.vfwebqq = ""
        self.uin_type = {}  # 提供uin到客户端类型的转换 (friend group discuss)
        self.group = {}  # 群
        self.discuss = {}  # 讨论组(正常的数据结构)
        # self.discuss_for_notice = {}  # 讨论组(用于单播的数据结构)
        self.master_qq = master_qq if master_qq else None
        self.master_discuss_name = master_discuss_name if master_discuss_name else None
        self.page_source = page_source if page_source is not None else ""
        self.proxies = proxies if proxies is not None else {}
        self.qq_to_uin_dict = qq_to_uin_dict if qq_to_uin_dict is not None else {}
        self.uin_to_qq_dict = uin_to_qq_dict if uin_to_qq_dict is not None else {}
        self.requests_sess = requests_sess if requests_sess is not None else requests_init_session()
        self.clientid = clientid if clientid else DEFAULT_WEBQQ_CLIENTID
        self.verbose_level = verbose_level
        self.retries_delay = retries_delay
        self.pull_msg_timeout = pull_msg_timeout
        self.max_retries_count = max_retries_count
        self.create_time = create_time if create_time else time()  # 这个session被创建的时间

        _ = kwargs  # 多余的参数,假装把它们用掉,省的pycharm报警告

        self.update_headers()

        apoutput_set_verbose_level(self.verbose_level)

        if self.master_qq is None:
            warnprint('管理员qq未设置,建议在初始化时指定 master_qq= 参数指定管理员qq')
