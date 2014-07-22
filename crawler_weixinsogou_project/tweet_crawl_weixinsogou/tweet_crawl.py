#!/usr/bin/python
# -*-coding:utf-8-*-


import urllib2
import time
import random
import re
import os
from datetime import datetime
from config import *
from threading import Thread
from tweet_searched_account_ids_set import searched_account_ids_set

THREAD_NUM = 5


def log(msg):
	print "[" + str(datetime.now()) + "] " + str(msg) + '\n'

def sleep_for_a_while_small():
	time.sleep(random.randint(3, 6))


def get_accountid_with_openid_in_redis_to_redis_set(tweet_accountid_set_name, searched_account_ids_set = set([])):
	"""
	Return a redis set tweet_accountid_set_name, in which each item is a string of (account_id sogou_openi)
	"""

	hash_keys = r.keys('hash_account_id_*')

	for hash_key in hash_keys:
		open_id = r.hget(hash_key, 'sogou_openid')
		if (open_id != 'NA' and open_id != None):
			account_id = r.hget(hash_key, 'account_id')

			# filter out the account_id having been searched
			if int(account_id) not in searched_account_ids_set:
				r.sadd(tweet_accountid_set_name, str(account_id) + ' ' + str(open_id))

	print "The total account_id to crawl for tweet is %d" % r.scard(tweet_accountid_set_name)



def build_req_by_proxy_ip(proxy_ip, url):
	"""
	Return a Request object used to connect with url
	"""
	proxy_support = urllib2.ProxyHandler(proxy_ip)
	opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler)
	urllib2.install_opener(opener)

	random_user_agent = random.choice(USER_AGENT_LIST)
	headers = { 'User-Agent' : random_user_agent }
	req = urllib2.Request(url, headers = headers)

	return req

def get_connect_by_other_proxy_ip(proxy_ip, url):
	"""
	Try other ips except proxy_ip
	"""

	print "try other proxy_ip ..."

	c = None

	# copy the total USER_AGENT_LIST
	remaining_ips = PROXY_LIST[:]

	print 'the old proxy_ip is -> ', proxy_ip

	if proxy_ip in remaining_ips:
		remaining_ips.remove(proxy_ip)
		print 'remaining_ips.......................->', remaining_ips
	else:
		return c

	# try all the proxy_ips until success
	for new_ip in remaining_ips:
		try:

			req = build_req_by_proxy_ip(new_ip, url)
			print 'new proxy_ip is ', str(new_ip)
			c = urllib2.urlopen(req)
			print 'new_ip success!'
			return c

		except  BaseException as urllib2_proxy_error:
			print "new_ip error: urllib2 proxy error " + str(urllib2_proxy_error.message)

	return c

def get_connect_by_proxyip_ua(url):
	"""
	Return a connect to the webpage, through proxy ip and faked user-agent
	"""

	c = None

	try:

		proxy_ip =random.choice(PROXY_LIST) #在proxy_ips中随机取一个ip
		req = build_req_by_proxy_ip(proxy_ip, url)

		print 'proxy_ip is ', str(proxy_ip)
		c = urllib2.urlopen(req)
		print "ccccccc----------------------> ", str(c)
		return c

	except BaseException as urllib2_proxy_error:
		print "error: urllib2 proxy error " + str(urllib2_proxy_error.message) + "the exception url is " + str(url)

		# try other proxy_ip
		c = get_connect_by_other_proxy_ip(proxy_ip, url)

		return c



def get_url_info_from_sogou(open_id):
	"""
	Return the url contains the tweet_url info in the sogou.com
	"""
	info_url = "http://weixin.sogou.com/gzhjs?cb=sogou.weixin.gzhcb&openid=" + open_id + "&page=1"
	return info_url




def get_weixinsogou_tweet_info_by_openid(open_id):
	"""
	Return a string, which is the tweet_info of a single open_id in sogou.com
	"""
	sogou_tweet_info_content = None

	tweet_info_url = get_url_info_from_sogou(open_id)

	# connect to the website with proxy_ip and faked user-agent
	con_tweet_info = get_connect_by_proxyip_ua(tweet_info_url)

	if con_tweet_info != None :
		sogou_tweet_info_content = con_tweet_info.read()

	return  sogou_tweet_info_content


def get_tweet_urls_by_content(sogou_tweet_info_content):
	"""
	Return a list of tweet_url, otherwise None
	"""


	reg_exp = r'<url><!\[CDATA\[(http://mp\.weixin\.qq\.com/.*?)]'

	all_tweet_urls = re.findall(reg_exp, sogou_tweet_info_content)

	if all_tweet_urls != None :
		return all_tweet_urls[: TWEET_NUM_TO_CRAWL]
	else:
		return None


def get_tweets_by_openid(open_id):
	"""
	Return a list of string, which is the tweet info
	"""

	latest_tweets = []
	
	sogou_tweet_info_content = get_weixinsogou_tweet_info_by_openid(open_id)
	if sogou_tweet_info_content == None : return None

	tweet_urls = get_tweet_urls_by_content(sogou_tweet_info_content)

	# if no tweet info just return nothing
	if tweet_urls == None : return None

	# first add sogou_tweet_info_content to latest_tweets
	latest_tweets.append(sogou_tweet_info_content)

	for tweet_url in tweet_urls:
		log('crawl open_id --> %s, the url is %s' % (open_id, tweet_url))
		weixin_tweet_content = None

		# connect to the website with proxy_ip and faked user-agent
		con_weixin_tweet_content = get_connect_by_proxyip_ua(tweet_url)

		if con_weixin_tweet_content != None:
			weixin_tweet_content = con_weixin_tweet_content.read()

		latest_tweets.append(weixin_tweet_content)

		sleep_for_a_while_small()

	return latest_tweets


def output_tweet_to_file(account_id, tweet_content_list):
	"""
	Output the tweet to local HTML file,
	the file name is based on the account_id and the content is the tweet.
	"""

	# set the file path
	# get the time 
	time_str = time.strftime('%Y%m%d')

	# get the last digit of the account_id as hash key to classifiy the account_id
	hash_key = int(account_id) % 10
	path_dir = './TWEET_HTML/' + time_str + '/' + str(hash_key) + '/' + str(account_id)

	try:
		# determine wheter the path is existed or not
		is_dir_existed = os.path.exists(path_dir)

		if (not is_dir_existed):
			# create the directory, and write header_str to the file
			log("The path is not existed, create a new one.")
			os.makedirs(path_dir)

		else:
			log("The path is existed, just open it and update the data.")

		for i in xrange(len(tweet_content_list)):
			if (i == 0): # store the info page
				file_path = path_dir + '/' + 'tweet_info_page.html'
			else:
				file_path = path_dir + '/' + 'tweet_' + str(i) + '.html'

	   		file_obj = open(file_path, 'w')
			file_obj.write(str(tweet_content_list[i]))
			file_obj.close()

	except BaseException as output_error:
		print "error: output_tweet_to_local_file " + output_error.message





def get_tweet_of_single_accountid_and_output_local_file():
	"""
	Crawl a sinle account_id's tweet info, and output to local file
	"""

	remaining_task = r.scard('tweet_accountid_set')

	while(remaining_task >= 1):
		# pop a open_id from the redis set 'tweet_accountid_set'
		account_info = r.spop('tweet_accountid_set')
		log('account_info ------------> ' + str(account_info)) 

		account_id, open_id = account_info.split()

		remaining_task = r.scard('tweet_accountid_set')


		log('-' * 10 + 'a new task starting  ' + '-' * 10)

		log("Current account_id is %s , open_id is %s, the remaining number of account_id to crawl is %d " % (str(account_id), str(open_id), remaining_task))


		tweet_content_list = get_tweets_by_openid(open_id)

		if tweet_content_list != None:
			output_tweet_to_file(account_id, tweet_content_list)

		


def get_all_tweet_and_output_to_file_by_tweet_accountid_set():
	"""
	Get all the tweet info by open_ids, and write them to local files
	"""

	n = r.scard('tweet_accountid_set')
	print "The total number of task is %d '\n'" % n

	threads = []
	for i in xrange(THREAD_NUM):
		t = Thread(target = get_tweet_of_single_accountid_and_output_local_file)
		t.setDaemon(True)
		threads.append(t)

	# start all the thread
	for t in threads:
		t.start()

	# Wait until all thread terminates
	for t in threads:
		t.join()


def main():
	log('STARTING CRAWLING TWEET ......')

	# write 
	
	if (r.scard('tweet_accountid_set') == 0): # there is no account_id left to crawl
		get_accountid_with_openid_in_redis_to_redis_set('tweet_accountid_set', searched_account_ids_set)

	get_all_tweet_and_output_to_file_by_tweet_accountid_set()
	log('FINISHING CRAWLING TWEET ......')

if __name__ == '__main__':
	res = main()

