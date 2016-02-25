# -*- coding: utf-8 -*-
from requests.cookies import RequestsCookieJar


def selenium2requests(selenium_cookie, req_cookies, is_clear_all=False):
    """
    Convert selenium-style cookies to requests-style cookies
    eg: req_session.cookies = selenium2requests(driver.get_cookies(),req_session.cookies)
    :type req_cookies: RequestsCookieJar
    :type selenium_cookie: list
    """
    if is_clear_all:
        req_cookies.clear()
    for c in selenium_cookie:
        req_cookies.set(c['name'], c['value'],
                        domain=(c['domain'] if 'domain' in c else ''),
                        path=(c['path'] if 'path' in c else '/'),
                        secure=(c['secure'] if 'secure' in c else False),
                        expires=(c['expiry'] if 'expiry' in c else None),
                        discard=(c['discard'] if 'discard' in c else True),
                        rest={'HttpOnly': (c['HttpOnly'] if 'HttpOnly' in c else False)},
                        port=(c['port'] if 'port' in c else None),
                        )
    return req_cookies
