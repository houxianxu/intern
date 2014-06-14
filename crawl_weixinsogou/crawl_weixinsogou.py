#!/usr/bin/python 
# -*-coding:utf-8-*-

# Description: crawl the weixin account infomation from http://weixin.sogou.com
# Version: 1.0
# History: 2014-06-10 Created by Hou

import urllib2
from bs4 import *
from datetime import datetime
import os
import time
import random
import re

keywords = ["时尚",
"母婴",
"搭配",
"潮流",
"奢饰品",
"互联网",
"IT",
"旅游",
"模特",
"艺人",
"时尚达人",
"搭配达人",
"潮流",
"秀场",
"原创搞笑",
"作家",
"写手",
"电商",
"互联网",
"网购",
"UC",
"数码",
"设计",
"媒体",
"MV",
"传媒",
"新闻",
"游戏",
"视频",
"网络",
"淘宝购物",
"手机",
"科技",
"营销",
"摄影",
"微博",
"理财",
"IT数码",
"iPhone",
"数码控",
"团购导航",
"移动互联网",
"IT互联网",
"新媒体",
"资讯",
"网络推广",
"ipad",
"Android",
"电脑",
"PC",
"新周刊",
"iphone4",
"商业",
"电子商务",
"APP",
"无线"]


def log(msg):
    print "[" + str(datetime.now()) + "] " + str(msg) + "\n"

def get_account_info(keywords):
    # get all the account url
    account_urls = get_account_url_by_nav_pages(keywords)

    # crawl info by single account website
    res_info = []
    url_num = len(account_urls)
    remain_num = url_num
    for url in account_urls:
        print ("Total url number is %d, remaining: %d" %(url_num, remain_num))
        remain_num -= 1

        try:
            single_info = get_single_account_info(url, keywords)

        except BaseException as e:
            log('error when get_single_account_info, cause %s' % e.message)
            print(url)

        res_info.append(single_info)

        sleep_for_a_while_small()

    return res_info


# return all the account, so far the max nav page number is 20
def get_account_url_by_nav_pages(keywords, max_page_number = 20):
    res_account = []
    for page_num in xrange(1, max_page_number + 1):
        log(keywords + " :crawl page %d ..." %page_num)
        tmp_account_list = get_account_url_by_single_nav_page(page_num, keywords)

        if (tmp_account_list == None):
            log("The max nav page for " + '\"' + keywords + '\"' + " is %d " %(page_num - 1))
            break

        res_account += tmp_account_list
        sleep_for_a_while_small()
    # print res_account
    return res_account


# return the first nav page url by keywords
def get_nav_page_url_by_keywords(keywords):
    return ["http://weixin.sogou.com/weixin?query=" + str(keywords) + "&type=1&ie=utf8&cid=null&page=", "&p=40040100&dp=1&w=01029901&dr=1"]


def get_account_url_by_single_nav_page(page_num, keywords):
    # get the soup
    tmp_nav_url = get_nav_page_url_by_keywords(keywords)
    nav_url = tmp_nav_url[0] + str(page_num) + tmp_nav_url[1]
    
    c = urllib2.urlopen(nav_url)
    soup_obj = BeautifulSoup(c.read())

    if (soup_obj == None):
        return None
    # print soup_obj.prettify()
    account_url_list = [] # store the result

    # parse the soup, and get the tag a
    all_a = soup_obj.find_all("a", class_ = "wx-rb bg-blue wx-rb_v1")

    for tag_a in all_a:
        account_url_list.append(get_account_url_by_single_tag(tag_a))

    if (len(account_url_list) == 0):
        return None
    else:
        return account_url_list


def get_account_url_by_single_tag(tag_a):
    return "http://weixin.sogou.com" + tag_a["href"]

def get_single_account_info(url, keywords):
    # connect the website and build soup
    account_info = []
    c = urllib2.urlopen(url)
    soup_obj = BeautifulSoup(c.read())

    if (soup_obj == None):
        return None
    
    # meet_require = is_meet_require(soup_obj)

    # if (not meet_require):
    #     return None
    # else:
    account_info = get_info_by_soup(soup_obj)
    # add url and keywords to account_info
    account_info["url"] = url
    account_info["keywords"] = keywords

    return account_info

def get_info_by_soup(soup_obj):
    # get the info div
    info_div = soup_obj.find("div", id = "sogou_vr__box_0")
    weixin_name = get_name_by_div(info_div)
    weixin_id = get_id_by_div(info_div)
    weixin_QRcode_url = get_QRcode_url(info_div)

    weixin_info = {}
    weixin_info["name"] = weixin_name
    weixin_info["id"] = weixin_id
    weixin_info["QRcode"] = weixin_QRcode_url

    return weixin_info


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

def get_QRcode_url(info_div):
    target_div = info_div.find("div", class_ = "v-box")
    QRcode_url = target_div.img['src']
    return QRcode_url


# # using the date to filter the account to crawl, given by a website of soup
# def is_meet_require(soup_obj, month_threshold = 1):
#     seconds_of_threshold = month_threshold * 30 * 24 * 60 * 60
#     time_now = time.time()
#     info_last_time = get_last_time(soup_obj)

#     if (time_now - info_last_time <= seconds_of_threshold):
#         return True
#     else:
#         return False


# def get_last_time(soup_obj):
#     target_div = soup_obj.find("div", id = "wxbox")
#     target_div =target_div.find("div", class_ = "zj-tit")
#     time_str = target_div.span.get_text()
#     if (time_str == "该公众号暂未发布文章"):
#         return 0 # don't crawl
#     else:
#         time_local = time.strptime(time_str, "%Y-%m-%d %H:%M")
#         time_seconds = time.mktime(time_local)
#         return time_seconds



def crawl_account_weixin_sogou_by_keyword(keywords):
    max_page_number = 20
    res_list = get_account_url_by_nav_pages(keywords, max_page_number)
    return res_list


# write the result to 
def output_items_into_file(result_items, file_path):
    file_obj = None

    try:
        file_obj = open(file_path, 'a+')
        item_index = 0
        for item in result_items:
            #write link content as page
            try:        
                # log("houxianxu")
                str_output = '\t'.join([str(item['name'].encode('utf-8')),
                                        str(item['id']),
                                        str(item['url']),
                                        str(item['QRcode']),
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
    time.sleep(random.randint(1, 5))

def sleep_for_a_while_small():
    time.sleep(random.randint(0, 1))


def main():
    file_path = "./user_weixinsogou_20140610.txt"
    log("STARTING.............................")

    file_obj = open(file_path, 'w')
    file_obj.write('\t'.join(["用户名", "微信号", "主页", "二维码", "关键字", "\n"]))
    file_obj.close()

    global keywords

    for keyword in keywords:
        result = get_account_info(keyword)
        output_items_into_file(result, file_path)

    log("ALL DONE!")

if __name__ == '__main__':
    main()



## test
# weixin_info = {}
# weixin_info["url"] = "11"
# weixin_info["name"] = "22"
# weixin_info["id"] = "33"
# weixin_info["QRcode"] = "44"
# tmp_list = []
# tmp_list.append(weixin_info)
# output_items_into_file(tmp_list, file_path)
# max_page_number = 20


