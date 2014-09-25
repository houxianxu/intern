#!/usr/bin/python
# -*-coding:utf-8-*-

# Description: helpful function for the user_account crawl,
#              both for account verification and new account crawl

# Version: 1.0
# History: 2014-07-04 Created by Hou

import time
import random
import re
from bs4 import *
from datetime import datetime
from config import *


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

    verified_type = 'NA'

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
    if (target_ps is not None):
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
