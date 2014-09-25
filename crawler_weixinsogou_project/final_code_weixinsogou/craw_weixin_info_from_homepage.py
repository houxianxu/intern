#!/usr/bin/python
# -*-coding:utf-8-*-

# Description: crawl the weixin acount_info from the home page on sogou.com

# Version: 1.0
# History: 2014-07-04 Created by Hou

import re
from bs4 import *
from config import *
from connect_with_proxy_ip_and_fake_ua import get_connect_by_proxyip_ua

# help function for getting info from info_div


def get_name_by_div(info_div):
    target_div = info_div.find("div", class_="txt-box")
    name = target_div.find(id="weixinname").get_text()
    name.encode("utf-8")
    return name


def get_id_by_div(info_div):
    target_div = info_div.find("div", class_="txt-box")
    id_text = target_div.h4.span.get_text()
    id_text = id_text.encode("utf-8")
    id_text = re.search("微信号：(.*)", id_text).group(1)
    return id_text


def get_touxiang_url_div(info_div):
    target_div = info_div.find('div', class_="img-box")
    tou_xiang_url = target_div.img.get('src')
    return tou_xiang_url


def get_verified_status_div(info_div):
    target_div = info_div.find('div', class_='img-box')
    return target_div.find("span", class_="ico-r") is not None


def get_QRcode_url_by_div(info_div):
    target_div = info_div.find("div", class_="v-box")
    QRcode_url = target_div.img['src']
    return QRcode_url


def get_func_description_div(info_div):
    target_divs = info_div.find_all('div', class_='s-p2')
    if (target_divs is not None):
        for target_div in target_divs:
            tag_span_text = target_div.get_text().encode('utf-8').strip()
            if re.search('^功能介绍.*', tag_span_text) is not None:
                return tag_span_text

    return 'NA'


def get_verified_type_by_target_div(target_div):
    """
    Return a string, indicating the verified type
    """

    verified_type = 'NA'

    target_text = target_div.find('script').get_text()

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


def get_verified_info(info_div):
    strict_info_div = info_div.find("div", class_="txt-box")
    target_divs = strict_info_div.find_all("div", class_="s-p2")

    if (target_divs is not None):
        for target_div in target_divs:
            target_div_text = target_div.get_text().encode("utf-8").strip()
            reg_exp = r'^authnamewrite.*?\)'
            if re.search(reg_exp, target_div_text) is not None:
                verified_type = get_verified_type_by_target_div(target_div)
                verified_info = re.sub(reg_exp, verified_type, target_div_text)
                return verified_info

    return 'NA'


def get_info_by_homepage_soup(soup_obj, url):
    # get the account info div
    info_div = soup_obj.find("div", id="sogou_vr__box_0")

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
        weibo_name = get_name_by_div(info_div)
        weibo_id = get_id_by_div(info_div)
        weibo_QRcode_url = get_QRcode_url_by_div(info_div)
        weibo_touxiang_url = get_touxiang_url_div(info_div)
        weibo_is_verified = get_verified_status_div(info_div)
        weibo_func_description = get_func_description_div(info_div)
        weibo_verified_info = get_verified_info(info_div)

        weibo_url = url
        weibo_sogou_openid = url.split('=')[-1]

    except BaseException as parse_error:
        print "parse_error in get_info_by_tag function" + parse_error.message

    finally:
        # using weibo_name to in accordance with the name in the MySQL
        weibo_info['weibo_name'] = weibo_name
        weibo_info['weibo_id'] = weibo_id
        weibo_info['home_page_url'] = weibo_url
        weibo_info['QR_code_url'] = weibo_QRcode_url
        weibo_info['keywords'] = weibo_name
        weibo_info['sogou_openid'] = weibo_sogou_openid
        weibo_info['tou_xiang_url'] = weibo_touxiang_url
        weibo_info['is_verified'] = weibo_is_verified
        weibo_info['verified_info'] = weibo_verified_info
        weibo_info['function_description'] = weibo_func_description

    return weibo_info


def get_single_account_info_by_homepage_url(url):
    # Return a list of two items
    # The first one indicates whether weibo_id found
    # The second is the all_info found for weibo_id
    # If not found return None

    c = get_connect_by_proxyip_ua(url)
    soup_obj = BeautifulSoup(c.read())

    if (soup_obj is None):
        return None

    account_info = get_info_by_homepage_soup(soup_obj, url)
    is_existed = True

    return (is_existed, account_info)


def main():
    url = 'http://weixin.sogou.com/gzh?openid=oIWsFt0ZcCHUsqATUWavAwn2Nl5s'

    weixin_info = get_single_account_info_by_homepage_url(url)
    return weixin_info


if __name__ == '__main__':
    tmp = main()
