#!/usr/bin/python
# -*-coding:utf-8-*-

# Description: connect to website with proxy ip and faked ua
# Version: 1.0
# History: 2014-07-25 Created by Hou

import urllib2
import random
from config import USER_AGENT_LIST, PROXY_LIST


def show_request_debug_log():
    """
    Print out the GET info when connect to website
    """
    httpHandler = urllib2.HTTPHandler(debuglevel=1)
    httpsHandler = urllib2.HTTPSHandler(debuglevel=1)
    opener = urllib2.build_opener(httpHandler, httpsHandler)
    urllib2.install_opener(opener)
    return opener


def build_req_by_proxy_ip(proxy_ip, url, debug_info=False):
    """
    Return a Request object used to connect with url
    """
    proxy_support = urllib2.ProxyHandler(proxy_ip)

    if (debug_info is False):
        opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler)
    else:
        print 'show the HTTP info ...'
        opener = show_request_debug_log()

    urllib2.install_opener(opener)

    random_user_agent = random.choice(USER_AGENT_LIST)
    headers = {'User-Agent': random_user_agent}
    req = urllib2.Request(url, headers=headers)

    return req


def get_connect_by_other_proxy_ip(proxy_ip, url, debug_info=False):
    """
    Try other ips except proxy_ip
    """

    print "try other proxy_ip ..."

    c = None

    # copy the total USER_AGENT_LIST
    remaining_ips = PROXY_LIST[:]

    print 'the old proxy_ip is -> ', proxy_ip

    if proxy_ip in remaining_ips:
        remaining_ips.remove(proxy_ip)
        print 'remaining_ips.......................->', remaining_ips
    else:
        return c

    # try all the proxy_ips until success
    for new_ip in remaining_ips:
        try:

            req = build_req_by_proxy_ip(new_ip, url, debug_info)
            print 'new proxy_ip is ', str(new_ip)
            c = urllib2.urlopen(req)
            print "connect succeed with new proxy_ip ", str(proxy_ip)
            return c

        except BaseException as urllib2_proxy_error:
            print("error: urllib2 proxy error " + str(urllib2_proxy_error.message) +
                  "the exception url is " + str(url) +
                  "the proxy_ip is " + str(proxy_ip))
    print('all proxy_ips are checked, however the connect still fails')
    return c


def get_connect_by_proxyip_ua(url, debug_info=False):
    """
    Return a connect to the webpage, through proxy ip and faked user-agent
    """

    c = None

    try:

        proxy_ip = random.choice(PROXY_LIST)  # 在proxy_ips中随机取一个ip
        req = build_req_by_proxy_ip(proxy_ip, url, debug_info)

        print 'proxy_ip is ', str(proxy_ip)
        c = urllib2.urlopen(req)
        print "connect succeed with proxy_ip ", str(proxy_ip)
        return c

    except BaseException as urllib2_proxy_error:
        print("error: urllib2 proxy error " + str(urllib2_proxy_error.message) +
              "the exception url is " + str(url) +
              "the proxy_ip is " + str(proxy_ip))

        # try other proxy_ip
        c = get_connect_by_other_proxy_ip(proxy_ip, url, debug_info)

        return c


def main():
    url = 'http://weixin.sogou.com/weixin?type=1&query=0&ie=utf8&_ast=1406272256&_asf=null&w=01019900&p=40040100&dp=1&cid=null&sut=2169&sst0=1406277342926&lkt=1%2C1406277342681%2C1406277342681'
    connect = get_connect_by_proxyip_ua(url)
    if connect is not None:
        print connect.read()
    else:
        print 'the connect fails, please check the ips or urls!'


if __name__ == '__main__':
    main()
