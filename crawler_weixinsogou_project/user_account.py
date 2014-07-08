#!/usr/bin/python
# -*-coding:utf-8-*-

# Description: verified the user account from mysql and write info to redis and local fileS
# Version: 1.0
# History: 2014-07-04 Created by Hou

import redis
import urllib2
import os
import time
import random
import re
import config
from bs4 import *
from datetime import datetime
from config import *

# global varible, redis host address


def log(msg):
    print "[" + str(datetime.now()) + "] " + str(msg) + '\n'

def get_header_list():
    """
    Return all the field for weibo info
    """

    return ["account_id", "weibo_name", "weibo_id", "home_page_url", "QR_code_url", "keywords",
            "sogou_openid", "tou_xiang_url", "function_description", "is_verified", "is_existed"]


def output_from_redis_to_file(file_path = './account_info_in_redis.csv'):
    """
    Output all the weibo_info crawled from weixin.sogou.com
    from the redis to local file
    """

    header_list = get_header_list()
    header_str = '\t'.join(header_list) + '\n'

    try:
        file_obj = open(file_path, 'w')
        file_obj.write(header_str)

        # get account_id from redis
        for account_id_tmp in r.keys('hash_account_id_*'):
            account_info_dic = r.hgetall(account_id_tmp)

            account_info_list = []
            for field in header_list:

                # get the weibo info, set 'NA' if not available
                account_info_list.append(account_info_dic.get(field, 'NA'))

            account_info_str = '\t'.join([str(i) for i in account_info_list]) + '\n'
            file_obj.write(account_info_str)


    except BaseException as output_error:
        print "error: output_from_redis_to_file " + output_error.message

    finally:
        file_obj.close()


def add_single_account_info_to_redis(account_id_tmp, all_info):
    """
    Add weibo_info of account which found on weixin.sogou.com to redis, 
    """

    # add account_id to hash
    # get rid of the prefix 
    all_info['account_id'] = account_id_tmp.split('_')[-1]
    for key in all_info.keys():
        r.hset(account_id_tmp, key, all_info[key])

def add_single_account_verified_false_to_redis(account_id_tmp):
    """
    Add weibo_info of account which not found on weixin.sogou.com to redis, 
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

            single_info_str = '\t'.join([str(i) for i in single_info_list]) + '\n'

            file_obj.write(single_info_str)

    except BaseException as output_error:
        print "error: output_new_account_to_local_file " + output_error.message

    finally:
        file_obj.close()




def get_name_by_tag(info_tag):
    target_div = info_tag.find("div", class_ = "txt-box")
    name = target_div.h3.get_text()
    name = name.encode("utf-8")
    return name

def get_id_by_tag(info_tag):
    target_div = info_tag.find("div", class_ = "txt-box")
    id_text = target_div.h4.get_text()
    id_text = id_text.encode("utf-8")
    id_text = re.search("微信号：(.*)", id_text).group(1)
    return id_text

def get_url_by_tag(info_tag):
    return "http://weixin.sogou.com" + info_tag["href"]

def get_QRcode_url_by_tag(info_tag):
    target_div = info_tag.find("div", class_ = "pos-ico")
    target_img = target_div.find('img', width='140', height='140')
    QRcode_url = target_img.get('src')
    return QRcode_url

def get_sogou_openid(info_tag):
    target_str = info_tag["href"] # e.g. href="/gzh?openid=oIWsFtyWEDMvUGlYY1e4QhGYTSvY"
    return target_str.split("=")[-1]

def get_touxiang_url(info_tag):
    target_div = info_tag.find("div", class_ = "img-box")
    tou_xiang_url = target_div.img['src']
    return tou_xiang_url

def get_verified_status(info_tag):
    target_div = info_tag.find("div", class_ = "img-box")
    if (target_div.find("span", class_ = "ico-r") != None):
        return True
    else:
        return False

def get_func_description(info_tag):
    target_div = info_tag.find("div", class_ = "txt-box")
    target_span = target_div.p.find("span", class_ = "sp-txt")
    return target_span.get_text().encode("utf-8")

def get_info_by_tag(info_tag, keywords):
    """
    Return a dictionary of all the info from an info_tag
    """

    # store the info
    weibo_info = {}

    weibo_name = get_name_by_tag(info_tag)
    weibo_id = get_id_by_tag(info_tag)
    weibo_url = get_url_by_tag(info_tag)
    weibo_QRcode_url = get_QRcode_url_by_tag(info_tag)
    weibo_sogou_openid = get_sogou_openid(info_tag)
    weibo_touxiang_url = get_touxiang_url(info_tag)
    weibo_is_verified = get_verified_status(info_tag)
    weibo_func_description = get_func_description(info_tag)

    weibo_info['weibo_name'] = weibo_name # using weibo_name to in accordance with the name in the MySQL
    weibo_info['weibo_id'] = weibo_id
    weibo_info['home_page_url'] = weibo_url
    weibo_info['QR_code_url'] = weibo_QRcode_url
    weibo_info['keywords'] = keywords
    weibo_info['sogou_openid'] = weibo_sogou_openid
    weibo_info['tou_xiang_url'] = weibo_touxiang_url
    weibo_info['is_verified'] = weibo_is_verified
    weibo_info['function_description'] = weibo_func_description
    return weibo_info

# return the first nav page url by keywords
def get_nav_page_url_by_keywords(keywords):
    return ["http://weixin.sogou.com/weixin?query=" + str(keywords) + "&type=1&ie=utf8&cid=null&page=", "&p=40040100&dp=1&w=01029901&dr=1"]


def show_request_debug_log():
    httpHandler = urllib2.HTTPHandler(debuglevel=1)  
    httpsHandler = urllib2.HTTPSHandler(debuglevel=1)  
    opener = urllib2.build_opener(httpHandler, httpsHandler)  
    urllib2.install_opener(opener)
    return opener

def get_connect_by_proxyip_ua(url):
    """
    Return a connect to the webpage, through proxy ip and faked user-agent
    """
    try:
        proxy_ip =random.choice(proxy_list) #在proxy_list中随机取一个ip
        print proxy_ip    
        proxy_support = urllib2.ProxyHandler(proxy_ip)
        opener = urllib2.build_opener(proxy_support,urllib2.HTTPHandler)
        urllib2.install_opener(opener)

    except BaseException as urllib2_proxy_error:
        print "error: urllib2 proxy error " + output_error.message

    finally: # do not use proxy
        ## show the debug log
        # opener = show_request_debug_log()
        # change the header user-agent
        random_user_agent = random.choice(USER_AGENT_LIST)
        headers = { 'User-Agent' : random_user_agent }   
        req = urllib2.Request(url, headers = headers)   
        c = urllib2.urlopen(req)
        return c

def get_info_by_single_nav_page(page_num, keywords, weibo_id):
    """
    Return a list of all the account info by single nav_page
    The first two elements are associated with weibo_id
    """

    # First set the is_existed to be False
    is_existed = False

    # the info of the weibo_id found on weixin.sogou.com
    existed_account_info = None

    # get the url by keywords
    tmp_nav_url = get_nav_page_url_by_keywords(keywords)
    nav_url = tmp_nav_url[0] + str(page_num) + tmp_nav_url[1]

    # connect to the website, and build soup
    # get connect to the website
    c = get_connect_by_proxyip_ua(nav_url)

    # build soup
    soup_obj = BeautifulSoup(c.read())

    if (soup_obj == None):
        return None

    # print soup_obj.prettify()

    # store the in account info
    account_info_list = []

    # parse the soup, and get the info tag
    all_div = soup_obj.find_all("div", class_ = "wx-rb bg-blue wx-rb_v1 _item")

    if (all_div == None):
        return None

    for info_div in all_div:

        # store all the info by single tag
        weibo_info = get_info_by_tag(info_div, keywords)

        # if find the same weibo_id, then set is_existed to be True, and store the info
        if (is_existed == False and weibo_info['weibo_id'] == weibo_id):
            print "The weibo_id has been found, set is_existed to be True"
            is_existed = True
            existed_account_info = weibo_info

        else:
            account_info_list.append(weibo_info)

    else:
        return (is_existed, existed_account_info, account_info_list)


def get_info_by_nav_pages(keywords, weibo_id, max_page_number = 2):
    """
    Return a list of all the account info by nav pages, so far the max nav page number is 20
    The first two elements are associated with weibo_id

    """

    # whether weibo_id is_existed in sogou.com
    is_existed = False

    # the info of the weibo_id found on weixin.sogou.com
    existed_account_info = None

    # store the result of all the info
    res_account_info = []

    for page_num in xrange(1, max_page_number + 1):

        log(keywords + " : crawl page %d ..." % page_num)

        # get and store the account info by single nav page
        tmp_account_list_is_existed = get_info_by_single_nav_page(page_num, keywords, weibo_id)

        if (tmp_account_list_is_existed == None):
            break # there is no page to crawl

        # if is_existed is False, then set is_existed to is_existed of new nav_page
        if (is_existed == False):
            is_existed = tmp_account_list_is_existed[0]
            existed_account_info = tmp_account_list_is_existed[1]

        other_account_info_list = tmp_account_list_is_existed[2]

        if (other_account_info_list == None): # there is no page to crawl
            log("The max nav page for " + '\"' + keywords + '\"' + " is %d " %(page_num - 1))
            break


        res_account_info += other_account_info_list

        sleep_for_a_while()

    return (is_existed, existed_account_info, res_account_info)


def get_account_info(keywords, weibo_id, hash_account_id):
    """
    Return all the account info by keywords searched on weixin.sogou.com
    """

    # if Redis has 'home_page_url' field, then crawl from the home page
    if (r.hexists(hash_account_id, 'home_page_url')):
        print "The home page url is existed, so just crawl from the homepage, not the keywords"
        home_page_url = r.hget(weibo_id, 'home_page_url')
        res_info = get_single_account_info_by_homepage_url(home_page_url)

    else:
        print "search by keywords"
        res_info = get_info_by_nav_pages(keywords, weibo_id)

    return res_info


def sleep_for_a_while():
    time.sleep(random.randint(0, 5))

def sleep_for_a_while_small():
    time.sleep(random.randint(0, 1))


############## get info from the weixin homepage on sogou.com ################      
def get_single_account_info_by_homepage_url(url, keywords):
    # connect the website and build soup
    account_info = []

    c = get_connect_by_proxyip_ua(url)
    soup_obj = BeautifulSoup(c.read())

    if (soup_obj == None):
        return None
    
    account_info = get_info_by_homepage_soup(soup_obj, url, keywords)
    is_existed = True

    return (is_existed, account_info, None)

# help function for getting info from info_div
def get_name_by_div(info_div):
    target_div = info_div.find("div", class_ = "txt-box")
    name = target_div.find(id = "weixinname").get_text()
    name.encode("utf-8")
    return name

def get_id_by_div(info_div):
    target_div = info_div.find("div", class_ = "txt-box")
    id_text = target_div.h4.span.get_text()
    id_text = id_text.encode("utf-8")
    id_text = re.search("微信号：(.*)", id_text).group(1)
    return id_text

def get_touxiang_url_div(info_div):
    target_div = info_div.find('div', class_ = "img-box")
    tou_xiang_url = target_div.img.get('src')
    return tou_xiang_url

def get_verified_status_div(info_div):
    target_div = info_div.find('div', class_ = 'img-box')
    return target_div.find("span", class_ = "ico-r") != None

def get_QRcode_url_by_div(info_div):
    target_div = info_div.find("div", class_ = "v-box")
    QRcode_url = target_div.img['src']
    return QRcode_url

def get_func_description_div(info_div):
    target_div = info_div.find('div', class_ = 's-p2')
    target_span = target_div.find('span', class_ = 'sp-txt')
    return target_span.get_text().encode('utf-8')

def get_info_by_homepage_soup(soup_obj, url, keywords):
    # get the account info div
    info_div = soup_obj.find("div", id = "sogou_vr__box_0")
 
    # store the info
    weibo_info = {}

    weibo_name = get_name_by_div(info_div)
    weibo_id = get_id_by_div(info_div)
    weibo_QRcode_url = get_QRcode_url_by_div(info_div)
    weibo_touxiang_url = get_touxiang_url_div(info_div)
    weibo_is_verified = get_verified_status_div(info_div)
    weibo_func_description = get_func_description_div(info_div)

    weibo_url = url
    weibo_sogou_openid = url.split('=')[-1]


    weibo_info['weibo_name'] = weibo_name # using weibo_name to in accordance with the name in the MySQL
    weibo_info['weibo_id'] = weibo_id
    weibo_info['home_page_url'] = weibo_url
    weibo_info['QR_code_url'] = weibo_QRcode_url
    weibo_info['keywords'] = keywords
    weibo_info['sogou_openid'] = weibo_sogou_openid
    weibo_info['tou_xiang_url'] = weibo_touxiang_url
    weibo_info['is_verified'] = weibo_is_verified
    weibo_info['function_description'] = weibo_func_description

    return weibo_info
############## end of get info from the weixin homepage on sogou.com ################  



######################## Main function ########################
def account_verify_by_weixin_sogou():
    """ 
    Verify account by weixin.sogou.com
    We add a new field --is_existed-- that indicated whether weibo_id is True  False
    is_existed = 1 if we find, and add all other infomation to redis
    """
    account_id_tmp = r.spop("account_id_set")

    while (account_id_tmp != None):

        account_id_tmp = 'hash_account_id_' + str(account_id_tmp)
        weibo_name = r.hget(account_id_tmp, "weibo_name")
        weibo_id = r.hget(account_id_tmp, "weibo_id")
        
        # print "houxianxu", account_id_tmp
        # print 'weibo_name', weibo_name
        # print 'weibo_id', weibo_id

        #  weibo_name as the keywords to search on the weixin.sogou.com
        all_info_by_account_id = get_account_info(weibo_name, weibo_id, account_id_tmp)

        #  whether the account existed on the weixin.sogou.com    
        is_existed = all_info_by_account_id[0]

        if (is_existed):
            # add is_existed field to redis to indicate found on weixin.sogou.com
            # 1 means found, otherwise 0

            r.hset(account_id_tmp, "is_existed", 1)
            # add other info crawled from weixin.sogou.com
            add_single_account_info_to_redis(account_id_tmp, all_info_by_account_id[1])

        else:
            add_single_account_verified_false_to_redis(account_id_tmp)

        # add new account not in the local database
        output_new_account_to_local_file(weibo_name, all_info_by_account_id[2])

        # next iteration
        account_id_tmp = r.spop("account_id_set")
