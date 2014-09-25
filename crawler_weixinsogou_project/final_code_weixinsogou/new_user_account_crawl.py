#!/usr/bin/python
# -*-coding:utf-8-*-

# Description: get new user_account info from weixin.sogou.com

# Version: 1.0
# History: 2014-07-04 Created by Hou

import os
import time
from threading import Thread
from bs4 import *
from config import *
from connect_with_proxy_ip_and_fake_ua import get_connect_by_proxyip_ua
from help_func_for_user_account_crawl import *


################### Main function for get new account ####################
def write_keywords_to_redis_set(keywords):
    for keyword in keywords:
        r.sadd('keywords_set', keyword)


def get_new_account_info_by_single_nav_page(page_num, keyword):
    """
    Return a tuple of 2 items
    The first is the info of a account
    The second is bool indicates whether is the last nav page
    """

    single_nav_info_list = []

    # get the url by keywords
    tmp_nav_url = get_nav_page_url_by_keywords(keyword)
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
    all_divs = soup_obj.find_all("div", class_="wx-rb bg-blue wx-rb_v1 _item")

    if (all_divs is None):
        return None

    for info_div in all_divs:

        # store all the info by single tag
        weibo_info = get_info_by_tag(info_div, keyword)

        if weibo_info is not None:
            single_nav_info_list.append(weibo_info)

    return (single_nav_info_list, is_last_page)


def get_new_account_info_by_nav_pages(keyword, max_page_number=20):
    """ search keyword on all pages on weixin.sogou.com

    Return a list of dict, which is the all_info found for keyword
    So far the max nav page number is 20
    """
    new_account_info_list = []

    for page_num in xrange(1, max_page_number + 1):

        log(str(keyword) + " : crawl page %d ..." % page_num)

        # get and store the account info by single nav page
        single_nav_info_list = get_new_account_info_by_single_nav_page(
            page_num, keyword)

        if (single_nav_info_list is None):
            log("The search is failed, check the url or the proxy_ips. \n")
            break

        account_info_list = single_nav_info_list[0]
        if account_info_list is not None:
            new_account_info_list.extend(account_info_list)

        # if it is the last page, then break
        is_last_page = single_nav_info_list[-1]
        if (is_last_page is True):
            log("The max nav page for " + '\"' +
                str(keyword) + '\"' + " is %d " % page_num)
            break

        sleep_for_a_while()

    return new_account_info_list


def get_header_list_for_new_account():
    """
    Return all the field for weibo info
    """

    return ["weibo_name", "weibo_id", "home_page_url", "QR_code_url",
            "sogou_openid", "tou_xiang_url", "function_description",
            "is_verified", "verified_info", "keywords"]


def output_new_account_to_local_file(new_account_info_list):
    """
    Output new account info to local file
    """

    # get header, new account has no account_id and is_existed
    header_list = get_header_list_for_new_account()
    header_str = '\t'.join(header_list) + '\n'

    # create new path and file to store the info
    time_str = time.strftime('%Y%m%d')
    path_dir = "./account/" + time_str
    file_path = path_dir + "/" + "new_weixin_account.tsv"

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
        for single_info in new_account_info_list:
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


def get_new_account_info_by_keywords_from_redis():

    total_num_keywords = r.scard('account_id_set')
    keyword = r.spop('keywords_set')

    while keyword is not None:
        log("The total number of keywords is " +
            str(total_num_keywords) +
            " , and remain number of keywords is " +
            str(r.scard('keywords_set')) +
            " , current keyword is " + str(keyword))

        new_account_info_list = get_new_account_info_by_nav_pages(keyword)

        if new_account_info_list is None or new_account_info_list == []:
            log('search failed, add the keyword to failed set in redis ' +
                'the keyword is ' + str(keyword))

            r.sadd("keyword_fail_set", keyword)
            keyword = r.spop('keywords_set')

            continue

        else:
            output_new_account_to_local_file(new_account_info_list)

        # next iteration
        keyword = r.spop('keywords_set')


def get_new_account_info_by_keywords(keywords):
    """ Get new weixin account from weixin.sogou.com by keywords
    Return a list of list of dict, which contains all the weixin_info
    """

    write_keywords_to_redis_set(keywords)  # keywords_set
    get_new_account_info_by_keywords_from_redis()


def get_new_account_with_multi_thread(keywords):
    """
    Verified the account with multi_thread
    """
    write_keywords_to_redis_set(keywords)

    threads = []
    for i in xrange(THREAD_NUM):
        t = Thread(target=get_new_account_info_by_keywords_from_redis)
        t.setDaemon(True)
        threads.append(t)

    # start all the thread
    for t in threads:
        t.start()

    # Wait until all thread terminates
    for t in threads:
        t.join()


def main():
    keywords = ['it', 'df', 'houxianxu', 'movie']
    # get_new_account_info_by_keywords(['IT', 'df', 'houxianxu'])
    get_new_account_with_multi_thread(keywords)

if __name__ == '__main__':
    main()
