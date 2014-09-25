#!/usr/bin/python
# -*-coding:utf-8-*-

# Description: get the tweet from mp.weixin.com, ans saved as HTML files

# Version: 1.0
# History: 2014-07-04 Created by Hou

import time
import random
import re
import os
from datetime import datetime
from config import *
from threading import Thread
from connect_with_proxy_ip_and_fake_ua import get_connect_by_proxyip_ua


def log(msg):
    print "[" + str(datetime.now()) + "] " + str(msg) + '\n'


def sleep_for_a_while_small():
    time.sleep(random.randint(3, 6))


def get_accountid_with_openid_in_redis_to_redis_set(tweet_accountid_set_name):
    """
    Return a redis set tweet_accountid_set_name,
    in which each item is a string of (account_id sogou_openi)
    """

    hash_keys = r.keys('hash_account_id_*')

    for hash_key in hash_keys:
        open_id = r.hget(hash_key, 'sogou_openid')
        if (open_id != 'NA' and open_id is not None):
            account_id = r.hget(hash_key, 'account_id')
            r.sadd(tweet_accountid_set_name, str(
                account_id) + ' ' + str(open_id))

    print ("The total account_id to crawl for tweet is %d"
           % r.scard(tweet_accountid_set_name))


def get_url_info_from_sogou(open_id):
    """
    Return the url contains the tweet_url info in the sogou.com
    """
    info_url = "http://weixin.sogou.com/gzhjs?cb=sogou.weixin.gzhcb&openid=" + \
        open_id + "&page=1"
    return info_url


def get_weixinsogou_tweet_info_by_openid(open_id):
    """
    Return a string, which is the tweet_info of a single open_id in sogou.com
    """
    sogou_tweet_info_content = None

    tweet_info_url = get_url_info_from_sogou(open_id)

    # connect to the website with proxy_ip and faked user-agent
    con_tweet_info = get_connect_by_proxyip_ua(tweet_info_url)

    if con_tweet_info is not None:
        sogou_tweet_info_content = con_tweet_info.read()

    return sogou_tweet_info_content


def get_tweet_urls_by_content(sogou_tweet_info_content):
    """
    Return a list of tweet_url, otherwise None
    """

    reg_exp = r'<url><!\[CDATA\[(http://mp\.weixin\.qq\.com/.*?)]'

    all_tweet_urls = re.findall(reg_exp, sogou_tweet_info_content)

    if all_tweet_urls is not None:
        return all_tweet_urls[: TWEET_NUM_TO_CRAWL]
    else:
        return None


def get_tweets_by_openid(open_id):
    """
    Return a list of string, which is the tweet info
    """

    latest_tweets = []

    sogou_tweet_info_content = get_weixinsogou_tweet_info_by_openid(open_id)
    if sogou_tweet_info_content is None:
        return None

    tweet_urls = get_tweet_urls_by_content(sogou_tweet_info_content)

    # if no tweet info just return nothing
    if tweet_urls is None:
        return None

    # first add sogou_tweet_info_content to latest_tweets
    latest_tweets.append(sogou_tweet_info_content)

    for tweet_url in tweet_urls:
        log('crawl open_id --> %s, the url is %s' % (open_id, tweet_url))
        weixin_tweet_content = None

        # connect to the website with proxy_ip and faked user-agent
        con_weixin_tweet_content = get_connect_by_proxyip_ua(tweet_url)

        if con_weixin_tweet_content is not None:
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

    # get the last digit of the account_id as hash key to classifiy the
    # account_id
    hash_key = int(account_id) % 10
    path_dir = ('./TWEET_HTML/' +
                time_str + '/' +
                str(hash_key) + '/' + str(account_id))

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
            if (i == 0):  # store the info page
                file_path = path_dir + '/' + 'tweet_info_page.html'
            else:
                file_path = path_dir + '/' + 'tweet_' + str(i) + '.html'

            file_obj = open(file_path, 'w')
            file_obj.write(str(tweet_content_list[i]))
            file_obj.close()

    except BaseException as output_error:
        print "error: output_tweet_to_local_file " + output_error.message


def get_all_tweet_and_output_to_file():
    """
    Crawl all account_id's tweet info per account_id, and output to local file
    """

    remaining_task = r.scard('tweet_accountid_set')

    while(remaining_task >= 1):
        # pop a open_id from the redis set 'tweet_accountid_set'
        account_info = r.spop('tweet_accountid_set')

        account_id, open_id = account_info.split()

        remaining_task = r.scard('tweet_accountid_set')

        log("Current account_id is %s , open_id is %s, \
            the remaining number of account_id to crawl is %d " %
            (str(account_id), str(open_id), remaining_task))

        tweet_content_list = get_tweets_by_openid(open_id)

        if tweet_content_list is not None:
            output_tweet_to_file(account_id, tweet_content_list)
        else:
            r.sadd('tweet_crawl_fail_set', account_id)

        sleep_for_a_while_small()


def get_all_tweet_and_output_to_file_with_multi_thread():
    """
    Get all the tweet info by open_ids, and write them to local files
    """

    n = r.scard('tweet_accountid_set')
    print "The total number of task is %d '\n'" % n

    threads = []
    for i in xrange(THREAD_NUM):
        t = Thread(target=get_all_tweet_and_output_to_file)
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

    # there is no account_id left to crawl
    if (r.scard('tweet_accountid_set') == 0):
        # store the account having home pages in redis
        get_accountid_with_openid_in_redis_to_redis_set('tweet_accountid_set')

    get_all_tweet_and_output_to_file_with_multi_thread()

    log('FINISHING CRAWLING TWEET ......')

if __name__ == '__main__':
    res = main()
