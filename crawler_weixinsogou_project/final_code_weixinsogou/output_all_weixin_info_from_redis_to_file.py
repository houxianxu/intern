#!/usr/bin/python
# -*-coding:utf-8-*-

# Description: output all weixin info in redis to local file
# Version: 1.0
# History: 2014-07-22 Created by Hou

import time
import sys
from datetime import datetime
from config import *

# deal with chinese characteristic
reload(sys)
sys.setdefaultencoding("utf8")


def log(msg):
    print "[" + str(datetime.now()) + "] " + str(msg) + '\n'


def get_header_list():
    """
    Return all the field for weibo info
    """

    return ["account_id", "weibo_name", "weibo_id", "home_page_url", "QR_code_url", "keywords",
            "sogou_openid", "tou_xiang_url", "function_description", "is_verified", "is_existed", "verified_info", 'tweet_latest_date']


def output_from_redis_to_file(file_path='./account_info_in_redis.tsv'):
    """
    Output all the weibo_info crawled from weixin.sogou.com
    from the redis to local file
    """

    header_list = get_header_list()

    header_str = '\t'.join(header_list) + '\n'

    print 'The header is ', header_str

    all_account_id_keys = r.keys('hash_account_id_*')
    total = len(all_account_id_keys)

    remain_account = total

    try:
        file_obj = open(file_path, 'w')
        file_obj.write(header_str)

        # get account_id from redis
        for account_id_tmp in r.keys('hash_account_id_*'):
            remain_account -= 1
            log('The total number of observation is ' + str(total) + ', ' + 'the remaining is ' + str(remain_account))

            account_info_dic = r.hgetall(account_id_tmp)

            account_info_list = []
            for field in header_list:

                # get the weibo info, set 'NA' if not available
                account_info_list.append(account_info_dic.get(field, 'NA').strip())

            account_info_str = '\t'.join([str(i) for i in account_info_list]) + '\n'
            file_obj.write(account_info_str)


    except BaseException as output_error:
        print "error: output_from_redis_to_file " + output_error.message

    finally:
        file_obj.close()


def main():
    time_str = time.strftime('%Y%m%d')
    output_from_redis_to_file('user_account_' + time_str + '.tsv')


if __name__ == '__main__':
    main()
