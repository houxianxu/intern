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
    target_div = info_tag.find("div", class_ = "v-box")
    QRcode_url = target_div.img['src']
    return QRcode_url

def get_info_by_tag(info_tag, keywords):
    weixin_info = {}

    weixin_name = get_name_by_tag(info_tag)
    weixin_id = get_id_by_tag(info_tag)
    weixin_url = get_url_by_tag(info_tag)
    weixin_QRcode_url = get_QRcode_url_by_tag(info_tag)

    weixin_info["name"] = weixin_name
    weixin_info["id"] = weixin_id
    weixin_info["url"] = weixin_url
    weixin_info["QRcode"] = weixin_QRcode_url
    weixin_info["keywords"] = keywords

    return weixin_info

# return the first nav page url by keywords
def get_nav_page_url_by_keywords(keywords):
    return ["http://weixin.sogou.com/weixin?query=" + str(keywords) + "&type=1&ie=utf8&cid=null&page=", "&p=40040100&dp=1&w=01029901&dr=1"]


def get_info_by_single_nav_page(page_num, keywords):
    # get the soup
    tmp_nav_url = get_nav_page_url_by_keywords(keywords)
    nav_url = tmp_nav_url[0] + str(page_num) + tmp_nav_url[1]
    
    c = urllib2.urlopen(nav_url)
    soup_obj = BeautifulSoup(c.read())

    if (soup_obj == None):
        return None
    # print soup_obj.prettify()
    account_info_list = [] # store the result

    # parse the soup, and get the tag a
    all_a = soup_obj.find_all("a", class_ = "wx-rb bg-blue wx-rb_v1")

    for tag_a in all_a:
        account_info_list.append(get_info_by_tag(tag_a, keywords))

    if (len(account_info_list) == 0):
        return None
    else:
        return account_info_list

# return all the account, so far the max nav page number is 20
def get_info_by_nav_pages(keywords, max_page_number = 20):
    res_account = []
    for page_num in xrange(1, max_page_number + 1):
        log(keywords + " : crawl page %d ..." %page_num)
        tmp_account_list = get_info_by_single_nav_page(page_num, keywords)

        if (tmp_account_list == None):
            log("The max nav page for " + '\"' + keywords + '\"' + " is %d " %(page_num - 1))
            break
        res_account += tmp_account_list

        sleep_for_a_while_small()

    return res_account


def get_account_info(keywords):
    # get the info by nav pages
    res_info = get_info_by_nav_pages(keywords)
    return res_info




# write the result to file
def output_items_into_file(result_items, file_path):
    file_obj = None

    try:
        file_obj = open(file_path, 'a+')
        item_index = 0
        for item in result_items:
            #write link content as page
            try:        
                # log("houxianxu")
                str_output = '\t'.join([str(item['name']),
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


def get_keywords():
    file_path = "./keywords_by_lin_weixin_sogou_20140614.txt"

    file_obj = open(file_path, 'r')
    keywords = []
    
    for line in file_obj:
        keyword = line.strip()
        keywords.append(keyword)

    file_obj.close()
    return keywords

def main():
    file_path = "./user_weixinsogou_lin_keywords_20140613.txt"
    log("STARTING.............................")

    file_obj = open(file_path, 'w')
    file_obj.write('\t'.join(["用户名", "微信号", "主页", "二维码", "关键字", "\n"]))
    file_obj.close()

    keywords = get_keywords()
    keywords_num = len(keywords)

    for keyword in keywords:
        print ("remaining keywords number is: %d" %keywords_num)
        keywords_num -= 1
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


