#!/usr/bin/python
# -*-coding:utf-8-*-

# Description: The main script for crawl project on weixin.sogou.com
# Version: 1.0
# History: 2014-07-04 Created by Hou

from mysql_to_redis import get_data_from_mysql_to_redis
from user_account_verification import account_verify_by_weixin_sogou
from config import *


# global varible, redis host address

def main():

    print ("START CRAWLING ...................................")
    # get account_id, weibo_id, weibo_name from MySQL, and write to Redis
    get_data_from_mysql_to_redis()

    # Set weibo_name as keywords, crawl on the weixin.sogou.com,
    # If the weibo_id is found on the web, then get all the account info,

    account_verify_by_weixin_sogou()

    print ("FINISH CRAWLING ..................................")


if __name__ == '__main__':
    main()
