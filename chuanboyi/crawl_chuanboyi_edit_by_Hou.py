# -*- coding: utf-8 -*-'
#
# Description:
# Version: 1.0
# History: 2012-12-22 Created By Xing.
# History: 2014-05-29 Edit by Hou

import urllib2
from bs4 import *
from datetime import datetime
import os
import time
import random
import re


def log(msg):
    print "[" + str(datetime.now()) + "] " + str(msg) + "\n"


#########################  page crawling  ##################################
def crawl_single_page(page):
    """

    """

    if page is None:
        page = 0

    log("Crawling chuanboyi Page=[%s]" % (str(page)))

    page_url = "http://www.chuanboyi.com/category-6-b0-min0-max0-attr0-" + str(page) + "-sell_number-DESC.html"

    c = urllib2.urlopen(page_url)

    #building soup for search
    #soup_obj = BeautifulSoup(c.read(), fromEncoding='gb18030')
    soup_obj = BeautifulSoup(c.read())
    account_list_within_page = parse_accounts_from_nav_page(soup_obj)
    final_result = list()
    for account_ref in account_list_within_page:
        try:
            # log("111")
            account_final_info = parse_single_account("http://www.chuanboyi.com/" + str(account_ref))
            # log("222")
            final_result.append(account_final_info)
        except BaseException as basic_error:
            log("skipping this account, cause: " + basic_error.message)

    return final_result


def parse_accounts_from_nav_page(navi_page_soup):
    if navi_page_soup is None:
        return None

    div_plist = find_div_by_id(navi_page_soup('div'), 'plist')

    account_list = list()

    for li in div_plist('li'):
        try:
            pname_div = find_div_by_class(li('div'), 'p-img')
            account_href = pname_div('a')[0]
            account_url = account_href.attrs['href']
            account_list.append(account_url)
        except:
            log("Skipping....")

    return account_list


def parse_single_account(account_ref):
    #sleep_for_a_while_small()

    c = urllib2.urlopen(account_ref)
    account_soup_obj = BeautifulSoup(c.read())
    detail_div = find_div_by_id(account_soup_obj('div'), 'detail')
    # print (detail_div)
    mc_force_div = find_div_by_class(detail_div('div'), 'mc fore tabcon')
    # log(mc_force_div)
    content_div = find_div_by_class(mc_force_div('div'), 'content')
    content_spans = content_div('span')
    # used to get weibo_url 
    content_as = content_div('a')

    account_direct_price = parse_single_account_price(account_soup_obj)

    weibo_url = find_item_from_spans_by_keyword(content_as, "weibo.com")
    # log(weibo_url)
    weibo_followers = find_item_from_spans_by_keyword(content_spans, "粉丝数量")

    weibo_info = dict()
    weibo_info['page'] = account_ref
    weibo_info['url'] = extract_content_by_regex(weibo_url, "(?P<url>http[:./0-9a-zA-Z]{3,})", 'url')
    
    weibo_info['followers'] = extract_content_by_regex(weibo_followers, "粉丝数量：(?P<followers>\\d{3,})", 'followers')
    # print account_direct_price
    weibo_info['price'] = extract_content_by_regex(account_direct_price, "￥(?P<price>(\\d|\\.){3,})", 'price')
    # print weibo_info
    if weibo_info['url'] is None or weibo_info['price'] is None:
        tmp_weibo_info = dict()
        tmp_weibo_info['page'] = account_ref
        return tmp_weibo_info
    else:
        return weibo_info


def parse_single_account_price(account_soup_obj):
    direct_price = find_div_by_id(account_soup_obj('strong'), 'goods_shop_price').text
    return direct_price.encode('UTF-8')


def find_item_from_spans_by_keyword(span_list, keyword):
    if span_list is None:
        return None

    for span in span_list:
        span_text = span.text.encode('utf-8')
        if span_text.find(keyword) > 0:
            return span_text.replace('&nbsp;', '')

    return None


def extract_content_by_regex(text, reg_exp, key):

    if text is None:
        return None

    matches = re.search(reg_exp, text, re.I | re.M)
    if matches and key in matches.groupdict():
        return matches.group(key)
    else:
        return None


def find_div_by_id(div_list, div_id):
    for div in div_list:
        if 'id' in dict(div.attrs) and dict(div.attrs)['id'] == div_id:
            return div

    return None


def find_div_by_class(div_list, class_id):
    for div in div_list:
        if 'class' in dict(div.attrs) and ' '.join(dict(div.attrs)['class']) == class_id:
            return div

    return None


#########################  file I/O  ##################################
def output_items_into_file(result_items, file_path):
    file_obj = None

    try:

        file_obj = open(file_path, 'a+')
        item_index = 0
        for item in result_items:

            #write link content as page
            try:
                if(item is None
                   or item['url'] is None
                   or item['price'] is None):
                    continue
                else:
                    # log("houxianxu")
                    str_output = '\t'.join([str(item['url']),
                                            str(item['price'])
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
    time.sleep(random.randint(1, 3))


########################## Main functions  #############################

filepath = "./user_chuanboyi_20140512.txt"
page_count = 58
log("STARTING.............................")

# write the header 
file_obj = open(filepath, 'w')
file_obj.write('\t'.join(["帐号", "价格"]) + "\n")
file_obj.close()

for page_id in range(1, page_count+1):
    try:
        # crawling
        accounts = crawl_single_page(page_id)

        
        output_items_into_file(accounts, filepath)

        # sleep for a while
        sleep_for_a_while()

    except BaseException as base_error:
        log('Error when crawling, cause: %s' % base_error.message)

log("ALL DONE!")

account_ref = "http://www.chuanboyi.com/7283.html"
parse_single_account(account_ref)