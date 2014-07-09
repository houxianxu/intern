#!/usr/bin/python
# -*-coding:utf-8-*-

# Description: Get weibo_id, weibo_name and account_id from MySOL database, and write to redis
# Version: 1.0
# History: 2014-07-04 Created by Hou

import MySQLdb
import sys
import os
import redis
import time
from datetime import datetime
from config import *

# deal with chinese characteristic
reload(sys)
sys.setdefaultencoding("utf8")


def clear_redis():
	"""
	Clear REDIS_HOST_ADDRESS redis
	"""
	r.flushall()

def log(msg):
    print "[" + str(datetime.now()) + "] " + str(msg) + '\n'

def get_account_info_from_mysql():
	"""
	Return a list of weibo info from MySOL sever
	The first element is the header, the second one is the data
	"""

	# connect to MySOL
	con = MySQLdb.connect(host = MYSQL_HOST, 
						  user = MYSQL_USER, 
						  passwd = MYSQL_PASSWD, 
						  db = MYSQL_DB, 
						  charset= MYSQL_CHARSET)

	# With the with keyword, the Python interpreter automatically releases the resources. 
	# It also provides error handling.
	with con:
		cur = con.cursor()

		# get account info from babysitter_account
		cur.execute("SELECT account_id, weibo_name, weibo_id\
					 FROM babysitter_account \
					 WHERE weibo_type = 9")

		# get the header
		desc = cur.description
		header_list = []

		for i in xrange(len(desc)):
			field = desc[i]		
			header_list.append(field[0])

		# the origin head_list -> ['account_id', 'weibo_name', 'weibo_id']
		# get the records
		data_list = list(cur.fetchall())
		return [header_list, data_list]


def output_from_mysql_to_redis(header_list, data_list):
	"""
	Return three redis data structure: 
		1. a SET of account_id
		2. a LIST of account_id
		2. HASHes of every account_id. all the other filds and value are keys and associated value
	"""
	
	# write all account_id into a redis set and list, and HASHes of every account_id
	for single_info in data_list:
		account_id_tmp = str(single_info[0])

		# add account_id in a set used for weixin.gogou.com
		r.sadd("account_id_set", account_id_tmp) 

		# add all info into hash table
		# we set the name of hash table as follows: 'hash_account_id_12345'
		hash_name_tmp = 'hash_account_id_' + str(account_id_tmp)
		r.hmset(hash_name_tmp, {header_list[1]: single_info[1], header_list[2]: single_info[2]})


def output_from_mysql_to_file(header_list, data_list, file_path):
	"""
	Write the account info from mysql to local file
	"""

	# get header string
	header_str = '\t'.join(header_list)
	file_obj = open(file_path, 'w')
	file_obj.write(header_str + '\n')

	for single_info in data_list:
		single_info = [str(i) for i in single_info]
		single_info_str = '\t'.join(single_info) + '\n'
		file_obj.write(single_info_str)

def get_data_from_mysql_to_redis():
	header_list, data_list = get_account_info_from_mysql()
	output_from_mysql_to_redis(header_list, data_list)



def unit_test_for_redis():
	header_list, data_list = get_account_info_from_mysql()
	# output_from_mysql_to_file(header_list, data_list, file_path)
	output_from_mysql_to_redis(header_list, data_list)
	

	print r.smembers("account_id_set")
	
	for id in r.smembers("account_id_set"):
		id = 'account_id_' + str(id)
		dic = r.hgetall(id)
		print id + " : "
		for key in dic.keys():

			print key + " -> " + dic[key]


def main():
	unit_test_for_redis()
	account_verify_by_weixin_sogou()
	output_from_redis_to_file("./temp.tsv")


if __name__ == '__main__':
	main()
