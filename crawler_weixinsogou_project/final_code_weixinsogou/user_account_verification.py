#!/usr/bin/python
# -*-coding:utf-8-*-

# Description: verified the user account from mysql, write weixin info to redis

# Version: 1.0
# History: 2014-07-04 Created by Hou

import time
import random
from threading import Thread
from bs4 import *
from config import *
from connect_with_proxy_ip_and_fake_ua import get_connect_by_proxyip_ua
from help_func_for_user_account_crawl import *
from craw_weixin_info_from_homepage import get_single_account_info_by_homepage_url


def sleep_for_a_while():
    time.sleep(random.randint(2, 6))


def sleep_for_a_while_small():
    time.sleep(random.randint(1, 3))


def add_single_account_info_to_redis(account_id_tmp, all_info):
    """
    Add weibo_info of account which found on weixin.sogou.com to redis
    """
    # add account_id to hash
    # get rid of the prefix
    all_info['account_id'] = account_id_tmp.split('_')[-1]
    for key in all_info.keys():
        r.hset(account_id_tmp, key, all_info[key])


def add_single_account_verified_false_to_redis(account_id_tmp):
    """
    Add weibo_info of account which not found on weixin.sogou.com to redis
    """

    # add account_id to hash
    # get rid of the prefix
    r.hset(account_id_tmp, "account_id", account_id_tmp.split('_')[-1])
    r.hset(account_id_tmp, "is_existed", 0)


def get_info_by_single_nav_page(page_num, keywords, weibo_id):
    """ Find weixin info in single nav_page on weixin.sogou.com

    Return a list of 3 items
    The first one indicates whether the account found
    The second is the info of the account
    The third one indicates whether is the last nav page
    """

    # First set the is_existed to be False
    is_existed = False

    # the info of the weibo_id found on weixin.sogou.com
    existed_account_info = 'NA'

    # get the url by keywords
    tmp_nav_url = get_nav_page_url_by_keywords(keywords)
    nav_url = tmp_nav_url[0] + str(page_num) + tmp_nav_url[1]

    print "nav_url ->  ", nav_url
    # connect to the website, and build soup
    # get connect to the website
    c = get_connect_by_proxyip_ua(nav_url)

    if (c is None):
        return None

    # build soup
    soup_obj = BeautifulSoup(c.read())

    if (soup_obj is None):
        return None

    is_last_page = is_last_page_by_soup(soup_obj)

    # print soup_obj.prettify()

    # parse the soup, and get the info tag
    all_div = soup_obj.find_all("div", class_="wx-rb bg-blue wx-rb_v1 _item")

    if (all_div is None):
        return None

    for info_div in all_div:

        # store all the info by single tag
        weibo_info = get_info_by_tag(info_div, keywords)

        # if find the same weibo_id, then set is_existed to be True, and store
        # the info
        if (is_existed is False and weibo_info['weibo_id'] == weibo_id):
            print "The weibo_id has been found, set is_existed to be True"
            is_existed = True
            existed_account_info = weibo_info

            return (is_existed, existed_account_info, is_last_page)

    return (is_existed, existed_account_info, is_last_page)


def get_info_by_nav_pages(keywords, weibo_id, max_page_number=20):
    """ search account info on all pages on weixin.sogou.com

    Return a list of two items
    The first one indicates whether weibo_id found
    The second is the all_info found for weibo_id
    So far the max nav page number is 20
    """

    # whether weibo_id is_existed in sogou.com
    is_existed = False

    # the info of the weibo_id found on weixin.sogou.com
    existed_account_info = 'NA'

    for page_num in xrange(1, max_page_number + 1):

        log(str(keywords) + " : crawl page %d ..." % page_num)

        # get and store the account info by single nav page
        single_nav_info_list = get_info_by_single_nav_page(
            page_num, keywords, weibo_id)

        if (single_nav_info_list is None):
            log("The connect is failed, check the url or the proxy_ips. \n")
            return None

        # if is_existed is False, set is_existed to is_existed of new nav_page
        if (is_existed is False and single_nav_info_list[0] is True):
            is_existed = single_nav_info_list[0]
            existed_account_info = single_nav_info_list[1]
            # found the account
            return (is_existed, existed_account_info)

        # if it is the last page, then break
        is_last_page = single_nav_info_list[-1]
        if (is_last_page is True):
            log("The max nav page for " + '\"' +
                str(keywords) + '\"' + " is %d " % page_num)
            break

        sleep_for_a_while()

    return (is_existed, existed_account_info)


def get_account_info(keywords, weibo_id, account_id_key):
    """
    Get all the account info by keywords searched on weixin.sogou.com

    Return a list of two items
    The first one indicates whether weibo_id found
    The second is the all_info found for weibo_id
    If not found return None
    """

    # if Redis has 'home_page_url' field, then crawl from the home page
    home_page_url = r.hget(account_id_key, 'home_page_url')
    if (home_page_url is not None and home_page_url != 'NA'):
        print "The home page url is existed, so just crawl from the homepage"
        print "The home_page_url is ", home_page_url
        res_info = get_single_account_info_by_homepage_url(home_page_url)

    else:
        print "The home page url is not existed, search in the search engine"
        res_info = get_info_by_nav_pages(keywords, weibo_id)

    return res_info


#################### Main function for account verification ##############
def account_verify_by_weixin_sogou():
    """Verify account by weixin.sogou.com
       add a new field named is_existed indicating whether weibo_id is found
       is_existed = 1 if we find, and add all other infomation to redis
    """

    account_id = r.spop("account_id_set")
    total_num_account = r.scard('account_id_set')

    while (account_id is not None):

        log("The total account_id is " + str(total_num_account) +
            " , and remain number of account is " +
            str(r.scard('account_id_set')))

        account_id_key = 'hash_account_id_' + str(account_id)
        weibo_name = r.hget(account_id_key, "weibo_name")
        weibo_id = r.hget(account_id_key, "weibo_id")

        print 'account_id_key -> ', account_id_key
        print 'weibo_name -> ', weibo_name

        #  weibo_name as the keywords to search on the weixin.sogou.com
        all_info_by_account_id = get_account_info(
            weibo_name, weibo_id, account_id_key)

        #  whether the account existed on the weixin.sogou.com
        if all_info_by_account_id is None:
            log('search failed, add the account to failed set in redis ' +
                'the account_id is ' + str(account_id))

            r.sadd("account_id_fail_set", account_id)
            continue

        is_existed = all_info_by_account_id[0]

        if (is_existed):
            # add is_existed field to redis indicating found on weixin.sogou.com
            # 1 means found, otherwise 0
            r.hset(account_id_key, "is_existed", 1)

            # add other info crawled from weixin.sogou.com
            add_single_account_info_to_redis(
                account_id_key, all_info_by_account_id[1])

        else:
            add_single_account_verified_false_to_redis(account_id_key)

        # next iteration
        account_id = r.spop("account_id_set")


def account_verified_with_multi_thread():
    """
    Verified the account with multi_thread
    """
    threads = []
    for i in xrange(THREAD_NUM):
        t = Thread(target=account_verify_by_weixin_sogou)
        t.setDaemon(True)
        threads.append(t)

    # start all the thread
    for t in threads:
        t.start()

    # Wait until all thread terminates
    for t in threads:
        t.join()


def main():
    account_verified_with_multi_thread()

if __name__ == '__main__':
    main()
