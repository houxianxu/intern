#!/usr/bin/python
# -*-coding:utf-8-*-

# Description: verified the user account from mysql, write weixin info to redis

# Version: 1.0
# History: 2014-07-04 Created by Hou

import os
import time
import random
import re
from threading import Thread
from bs4 import *
from datetime import datetime
from config import *
from connect_with_proxy_ip_and_fake_ua import get_connect_by_proxyip_ua


def log(msg):
    print "[" + str(datetime.now()) + "] " + str(msg)


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


def output_new_account_to_local_file(keywords, all_info_by_account):
    """
    Output new account info to local file
    """

    # get header, new account has no account_id and is_existed
    header_list = get_header_list()[1: -1]
    header_str = '\t'.join(header_list) + '\n'

    # create new path and file to store the info
    time_str = time.strftime('%Y%m%d')
    path_dir = "./account/" + "weixin_user_" + time_str
    file_path = path_dir + "/" + "weixin_sogou_account.tsv"

    try:
        # determine wheter the path is existed or not
        is_dir_existed = os.path.exists(path_dir)

        if (not is_dir_existed):
            # create the directory, and write header_str to the file
            log("the path is not existed, create a new one")
            os.makedirs(path_dir)
            file_obj = open(file_path, 'w')
            file_obj.write(header_str)

        else:
            log("the path is existed")
            # open the file as append mode --> no header_str
            file_obj = open(file_path, 'a')

        # write all the new account info to file
        for single_info in all_info_by_account:
            single_info_list = []

            # get single account info based on header_list
            for field in header_list:
                single_info_list.append(single_info.get(field, 'NA'))

            single_info_str = '\t'.join(
                [str(i) for i in single_info_list]) + '\n'

            file_obj.write(single_info_str)

    except BaseException as output_error:
        print "error: output_new_account_to_local_file " + output_error.message

    finally:
        file_obj.close()


def get_name_by_tag(info_tag):
    target_div = info_tag.find("div", class_="txt-box")
    name = target_div.h3.get_text()
    name = name.encode("utf-8")
    return name


def get_id_by_tag(info_tag):
    target_div = info_tag.find("div", class_="txt-box")
    id_text = target_div.h4.get_text()
    id_text = id_text.encode("utf-8")
    id_text = re.search("微信号：(.*)", id_text).group(1)
    return id_text


def get_url_by_tag(info_tag):
    return "http://weixin.sogou.com" + info_tag["href"]


def get_QRcode_url_by_tag(info_tag):
    target_div = info_tag.find("div", class_="pos-ico")
    target_img = target_div.find('img', width='140', height='140')
    QRcode_url = target_img.get('src')
    return QRcode_url


def get_sogou_openid(info_tag):
    # e.g. href="/gzh?openid=oIWsFtyWEDMvUGlYY1e4QhGYTSvY"
    target_str = info_tag["href"]
    return target_str.split("=")[-1]


def get_touxiang_url(info_tag):
    target_div = info_tag.find("div", class_="img-box")
    tou_xiang_url = target_div.img['src']
    return tou_xiang_url


def get_verified_status(info_tag):
    target_div = info_tag.find("div", class_="img-box")
    if (target_div.find("span", class_="ico-r") is not None):
        return True
    else:
        return False


def get_func_description(info_tag):
    target_div = info_tag.find("div", class_="txt-box")
    target_ps = target_div.find_all("p", class_="s-p3")
    if (target_ps):
        for target_p in target_ps:
            tag_p_text = target_p.get_text().encode("utf-8").strip()
            if re.search('^功能介绍.*', tag_p_text) is not None:
                return tag_p_text
    return 'NA'


def get_verified_type_by_target_p(target_p):
    """
    Return a string, indicating the verified type
    """

    verified_type = None

    target_text = target_p.find('script').get_text()

    # get the type number based on weixin.sogou
    reg_exp = r'authnamewrite\(\'(\d)\'\)'
    type_number = int(re.search(reg_exp, target_text).group(1))

    if type_number == 1:
        verified_type = '腾讯'
    elif type_number == 4:
        verified_type = '新浪'
    else:
        verified_type = '微信'

    return verified_type


def get_verified_info(info_tag):
    target_div = info_tag.find("div", class_="txt-box")
    target_ps = target_div.find_all("p", class_="s-p3")
    if (target_ps):
        for target_p in target_ps:
            tag_p_text = target_p.get_text().encode("utf-8").strip()
            reg_exp = r'^authnamewrite.*?\)'
            if re.search(reg_exp, tag_p_text) is not None:
                verified_type = get_verified_type_by_target_p(target_p)
                # print tag_p_text
                verified_info = re.sub(reg_exp, verified_type, tag_p_text)
                return verified_info

    return 'NA'


def get_info_by_tag(info_tag, keywords):
    """
    Return a dictionary of all the info from an info_tag
    """
    # store the info
    weibo_info = {}

    weibo_name = 'NA'
    weibo_id = 'NA'
    weibo_url = 'NA'
    weibo_QRcode_url = 'NA'
    weibo_sogou_openid = 'NA'
    weibo_touxiang_url = 'NA'
    weibo_is_verified = 'NA'
    weibo_func_description = 'NA'
    weibo_verified_info = 'NA'

    try:
        weibo_name = get_name_by_tag(info_tag)
        weibo_id = get_id_by_tag(info_tag)
        weibo_url = get_url_by_tag(info_tag)
        weibo_QRcode_url = get_QRcode_url_by_tag(info_tag)
        weibo_sogou_openid = get_sogou_openid(info_tag)
        weibo_touxiang_url = get_touxiang_url(info_tag)
        weibo_is_verified = get_verified_status(info_tag)
        weibo_func_description = get_func_description(info_tag)
        weibo_verified_info = get_verified_info(info_tag)

    except BaseException as parse_error:
        print "parse_error in get_info_by_tag function" + parse_error.message

    finally:
        # using weibo_name to in accordance with the name in the MySQL
        weibo_info['weibo_name'] = weibo_name
        weibo_info['weibo_id'] = weibo_id
        weibo_info['home_page_url'] = weibo_url
        weibo_info['QR_code_url'] = weibo_QRcode_url
        weibo_info['keywords'] = keywords
        weibo_info['sogou_openid'] = weibo_sogou_openid
        weibo_info['tou_xiang_url'] = weibo_touxiang_url
        weibo_info['is_verified'] = weibo_is_verified
        weibo_info['verified_info'] = weibo_verified_info
        weibo_info['function_description'] = weibo_func_description

        return weibo_info

# return the first nav page url by keywords


def get_nav_page_url_by_keywords(keywords):
    return ["http://weixin.sogou.com/weixin?query=" +
            str(keywords) +
            "&type=1&ie=utf8&cid=null&page=",
            "&p=40040100&dp=1&w=01029901&dr=1"]


def is_last_page_by_soup(soup_obj):
    target_div = soup_obj.find('div', id='pagebar_container')
    if (target_div is None):
        return True
    else:
        next_tag_a = target_div.find('a', id='sogou_next')
        if next_tag_a is not None:
            return False
        else:
            return True


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
    existed_account_info = None

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
    existed_account_info = None

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
    Return all the account info by keywords searched on weixin.sogou.com
    """

    # if Redis has 'home_page_url' field, then crawl from the home page
    home_page_url = r.hget(account_id_key, 'home_page_url')
    if (home_page_url is not None and home_page_url != 'NA'):
        print "The home page url is existed, so just crawl from the homepage"
        print "The home_page_url is ", home_page_url
        # res_info = get_single_account_info_by_homepage_url(home_page_url)

    else:
        print "The home page url is not existed, search in the search engine"
        res_info = get_info_by_nav_pages(keywords, weibo_id)

    return res_info


######################## Main function ########################
def account_verify_by_weixin_sogou():
    """Verify account by weixin.sogou.com
       add a new field named is_existed indicating whether weibo_id is found
       is_existed = 1 if we find, and add all other infomation to redis
    """

    account_id = r.spop("account_id_set")

    while (account_id is not None):

        print "The remain number of account is %d" % r.scard('account_id_set')
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
            log('connected failed, add the account to failed set in redis')
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

# if __name__ == '__main__':
#     main()
