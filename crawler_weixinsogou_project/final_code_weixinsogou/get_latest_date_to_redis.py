#!/usr/bin/python
# -*-coding:utf-8-*-

# Description: The script is to get the latest date of account_id, based on the tweet they have sent.
# The tweet is crawled from the weixin.sogou.com, and saved as HTML files,

# Version: 1.0
# History: 2014-07-20 Created by Hou

from bs4 import *
from config import r
import os
import sys
from datetime import datetime


def log(msg):
    print "[" + str(datetime.now()) + "] " + str(msg) + '\n'


def get_all_account_id_by_tweet(sub_dir):
    return os.listdir(sub_dir)


def get_latest_tweet_file(latest_tweet_file_dir):
    latest_tweet_file = None

    file_exited = os.path.exists(latest_tweet_file_dir + 'tweet_1.html')
    if file_exited is True:
        latest_tweet_file = 'tweet_1.html'
    else:
        print "The latest tweet file tweet_1.html is not existed"

    return latest_tweet_file


def get_date_by_tweet(latest_tweet_file_path):
    """
    Return the date string from the target html file
    """

    tweet_date = None

    file_object = open(latest_tweet_file_path, 'r')

    soup_obj = BeautifulSoup(file_object)

    try:
        target_span = soup_obj.find('span', id="post-date")
        tweet_date = target_span.get_text().strip()

    except BaseException as beautifulsoup_error:
        print "error: get_date_by_tweet in parsing html " + beautifulsoup_error.message

    finally:
        file_object.close()

    return tweet_date


def get_latest_date_for_single_account_id(account_id, sub_dir):
    """
    Return a string, which is latest date of tweet sent by account_id
    """

    latest_date = None

    latest_tweet_file_dir = sub_dir + str(account_id) + '/'
    latest_tweet_file = get_latest_tweet_file(latest_tweet_file_dir)

    if latest_tweet_file is not None:
        latest_tweet_file_path = latest_tweet_file_dir + \
            '/' + latest_tweet_file
        latest_date = get_date_by_tweet(latest_tweet_file_path)

    return latest_date


def get_latest_date_by_tweets_by_sub_dir(sub_dir):
    account_ids_by_sub_dir = get_all_account_id_by_tweet(sub_dir)
    print 'account_ids_by_sub_dir-> ', account_ids_by_sub_dir
    latest_date_dict_by_sub_dir = {}

    # get all subdirectory date info
    for account_id in account_ids_by_sub_dir:
        latest_date = get_latest_date_for_single_account_id(
            account_id, sub_dir)
        latest_date_dict_by_sub_dir[str(account_id)] = latest_date

    return latest_date_dict_by_sub_dir


def get_latest_date_by_tweets_for_all_account_ids(tweet_path):
    """
    Return a dict, the key is the account_id, and the value is the latest date of tweet
    """

    # result dict
    latest_date_dict = {}

    # get the date by subdirectory
    for i in xrange(10):
        log('The current sub_dir is %d ' % i)

        # get all the account_id in subdirectory
        sub_dir = tweet_path + str(i) + '/'
        latest_date_dict_by_sub_dir = get_latest_date_by_tweets_by_sub_dir(
            sub_dir)

        # update the result dict
        latest_date_dict.update(latest_date_dict_by_sub_dir)

    return latest_date_dict


def output_latest_date_to_redis(latest_dates_with_account_id):
    for account_id, date in latest_dates_with_account_id.iteritems():
        account_id_key = 'hash_account_id_' + str(account_id)
        r.hset(account_id_key, new_field, latest_date)


def main():
    tweet_path = sys.argv[1]

    latest_dates_with_account_id = get_latest_date_by_tweets_for_all_account_ids(tweet_path)

    output_latest_date_to_redis(latest_dates_with_account_id)


if __name__ == '__main__':
    main()
