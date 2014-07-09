#!/usr/bin/python 
# -*-coding:utf-8-*-

# Description: crawl the weixin account infomation from http://weixin.sogou.com
# Version: 1.1
# History: 2014-06-10 Created by Hou --> crawl from the personal page of a single account
#          2014-06-13 Edited by Hou --> crawl just in the search pages


import urllib2
from bs4 import *
from datetime import datetime
import os
import time
import random
import re


def log(msg):
    print "[" + str(datetime.now()) + "] " + str(msg) + "\n"



# help function for getting info from info_tag
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
    c = urllib2.urlopen(nav_url)
    soup_obj = BeautifulSoup(c.read())
    if (soup_obj == None):
        return None

    # print soup_obj.prettify()

    # store the in account info
    account_info_list = []

    # parse the soup, and get the info tag
    all_a = soup_obj.find_all("a", class_ = "wx-rb bg-blue wx-rb_v1")

    if (all_a == None):
        return None

    for tag_a in all_a:
        # store all the info by single tag
        weibo_info = get_info_by_tag(tag_a, keywords)

        # if find the same weibo_id, then set is_existed to be True, and store the info
        if (is_existed == False and weibo_info['weibo_id'] == weibo_id):
            is_existed = True
            existed_account_info = weibo_info

        else:
            account_info_list.append(weibo_info)

    else:
        return (is_existed, existed_account_info, account_info_list)


def get_info_by_nav_pages(keywords, weibo_id, max_page_number = 20):
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


def get_account_info(keywords, weibo_id):
    """
    Return all the account info by keywords searched on weixin.sogou.com
    """
    res_info = get_info_by_nav_pages(keywords, weibo_id)
    return res_info


def output_items_into_file(result_items, file_path):
    """
    Write the result to file
    """
    file_obj = None

    try:
        file_obj = open(file_path, 'a+')
        item_index = 0
        for item in result_items:
            #write link content as page
            try:        
                # log("houxianxu")
                str_output = '\t'.join([str(item['weibo_name']),
                                        str(item['weibo_id']),
                                        str(item['home_page_url']),
                                        str(item['QR_code_url']),
                                        str(item['keywords']),
                                        ])

                file_obj.write(str_output + "\n")

            except BaseException as page_error:
                print(item)
                log('error when output_items_into_file, cause %s' % page_error.message)

            #increase index
            item_index += 1

    except BaseException as output_error:
        log(output_error.message)

    finally:
        if file_obj is not None:
            file_obj.close()


def sleep_for_a_while():
    time.sleep(random.randint(0, 5))

def sleep_for_a_while_small():
    time.sleep(random.randint(0, 1))


def get_keywords():
    file_path = "./keywords2_user_weixinsogou_20140610.txt"

    file_obj = open(file_path, 'r')
    keywords = []
    
    for line in file_obj:
        keyword = line.strip()
        keywords.append(keyword)

    file_obj.close()
    return keywords

def main():
    # file_path = "./user_weixinsogou_keywords2_20140616.txt"
    log("STARTING.............................")

    print get_account_info("女性心计学", "mmxuexi")
    # file_obj = open(file_path, 'w')
    # file_obj.write('\t'.join(["用户名", "微信号", "主页", "二维码", "关键字", "\n"]))
    # file_obj.close()

    # keywords = get_keywords()
    # keywords_num = len(keywords)

    # for keyword in keywords:
    #     print ("remaining keywords number is: %d" %keywords_num)
    #     keywords_num -= 1
    #     result = get_account_info(keyword)
    #     output_items_into_file(result, file_path)

    # log("ALL DONE!")

if __name__ == '__main__':
    main()



## test
# weibo_info = {}
# weibo_info["url"] = "11"
# weibo_info["name"] = "22"
# weibo_info["id"] = "33"
# weibo_info["QRcode"] = "44"
# tmp_list = []
# tmp_list.append(weibo_info)
# output_items_into_file(tmp_list, file_path)
# max_page_number = 20

# nav_url = "http://weixin.sogou.com/weixin?query=%E7%94%B5%E5%BD%B1&_asf=www.sogou.com&_ast=1404264585&w=01019900&p=40040100&ie=utf8&type=1"


