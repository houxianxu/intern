#!/usr/bin/python
# -*-coding:utf-8-*-

# Description: The main script for crawl project on weixin.sogou.com
# Version: 1.0
# History: 2014-07-04 Created by Hou

from mysql_to_redis import get_data_from_mysql_to_redis, clear_redis
from user_account import account_verify_by_weixin_sogou
from user_account import output_from_redis_to_file
from config import *



# global varible, redis host address

def main():
	clear_redis()
	# get account_id, weibo_id, weibo_name from MySQL, and write to Redis
	get_data_from_mysql_to_redis()

	
	# Regrard weibo_name as keywords, crawl on the weixin.sogou.com,
	# If find the weibo_id on the web, then get all the account info,
	# then write to redis, and output other account info to local files
	account_verify_by_weixin_sogou()

	output_from_redis_to_file()




if __name__ == '__main__':
	main()