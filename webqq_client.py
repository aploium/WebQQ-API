# -*- coding: utf-8 -*-
import socket
import threading

DEFAULT_PORT = 34567
__VERSION__ = '0.1.0'


def assembly_payload(paras):
    buffer = []
    for key in paras:
        buffer.append('_%s_=_{{{{%s}}}}_&' % (str(key), str(paras[key])))

    return (''.join(buffer)).encode()


class WebqqClient:
    def _send_and_receive(self, payload):
        """
        send bytes to server and receive echo

        :type payload: bytes
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server, self.port))
        except:
            return False
        self.socket.send(payload)
        buffer = []
        while True:
            d = self.socket.recv(1024)
            buffer.append(d)
            if len(d) < 1024:
                break
        self.socket.close()
        data = b''.join(buffer)
        try:
            data = data.decode(encoding='utf-8')
        except:
            data = data.decode(encoding='gbk')
        return data

    def handshake(self):
        payload = assembly_payload({
            'token': self.token,
            'cmd': 'handshake'
        })
        result = self._send_and_receive(payload)
        if 'handshakeOK' in result:
            return True

    def send_to_discuss(self, msg_content, target_discuss_name=None):
        target_discuss_name = target_discuss_name if target_discuss_name is not None else self.target
        if target_discuss_name is None:
            print('[ERR] an target discuss name must be given')
            return False
        payload = assembly_payload({
            'token': self.token,
            'cmd': 'sendtodis',
            'msg': msg_content,
            'target': target_discuss_name
        })
        result = self._send_and_receive(payload)
        if 'thank you' in result:
            return True
        else:
            return False

    def send_to_discuss_mt(self, msg_content, target_discuss_name=None):
        """
        an multi-threads version of send_to_discuss(), avoid lagging
        """
        s = threading.Thread(target=self.send_to_discuss, args=(msg_content, target_discuss_name))
        s.start()

    def write(self, stream):
        self._default_send_method(stream)
        return

    def __init__(self, server, token="", target=None, default_target_type='discuss', port=DEFAULT_PORT):
        self.server = server
        self.token = token
        self.target = target
        self.port = port
        if default_target_type == 'discuss':
            self._default_send_method = self.send_to_discuss
        if self.target is None:
            print('[TIP] In personal use, you can give a target=YOUR_QQ param.')
        if not self.token:
            print('[WARN] maybe you forget your token')
        if not self.handshake():
            print('[ERR] handshake error')


if __name__ == '__main__':
    from time import time

    server = '127.0.0.1'
    target = 'Xno0Pu7bnCB'
    token = 'apl'
    q_client = WebqqClient(server, token=token, target=target)
    q_client.send_to_discuss(time())
