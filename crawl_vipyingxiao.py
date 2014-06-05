# -*- coding: utf-8 -*-
#
# Description: Crawl from http://www.vipyingxiao.com/v/weixin.html
# Version: 1.0
# Platform: Ubuntu 12.04 LTS
# History: 2014-05-22 Created By Hou Xianxu
#

import urllib2
from bs4 import *
from datetime import datetime

def log(msg):
	print "[" + str(datetime.now()) + "] " + str(msg) + "\n"


def crawl_single_page(page_url):
	"""
	Just one page!
	"""
	# open the url
	c = urllib2.urlopen(page_url)

	# building soup for searh
	soup_obj = BeautifulSoup(c.read())

	# get all the table row element stored in a list
	all_tr_obj = soup_obj('tr')
	 

	# crawl data by table rows
	all_data_list = [] # list of list 

	# get col names
	col_names_tr = all_tr_obj[1]
	col_names = find_from_single_tr(col_names_tr)
	all_data_list.append(col_names)

	# get data
	for i in xrange(2, len(all_tr_obj)):
		tmp_data = find_from_single_tr(all_tr_obj[i])
		all_data_list.append(tmp_data)

	return all_data_list


# crawl_single_tr
def find_from_single_tr(tag_tr):
	res_header = []
	BASE_URL = "http://www.vipyingxiao.com/v/"

	for child in tag_tr.children:
		if (child != '\n' and child.get_text() != ''): # note that the result is like ---> [u'\n', <td class="xl68" style="border-top:none;border-left:none;width:93pt" width="124">趋势图</td>]
			target_text = child.get_text().encode('utf-8')

			if (child.a != None):
				target_text = BASE_URL + child.a["data-showpic"]
				# print target_text
			res_header.append(target_text)

	return res_header


def output_items_into_file(all_data_list, file_path):
	file_obj = None

	try:
		# open the file to write
		file_obj = open(file_path, 'w')

		for item in all_data_list:
				# an item per line
			try:
				str_output = '\t'.join(item)
				file_obj.write(str_output + '\n')

			except BaseException as page_error:
				log("error when output_items_into_file, cause %s " % page_error.message)

	except BaseException as output_error:
		log(output_error.message)

	finally:
		if file_obj is not None:
			file_obj.close()



#################### Main functions ####################
def main():

	file_path = "/media/bigData/weiboyi/AccountCrawler/src/app/user_vipyingxiao_20140523.txt" # user_dfdsf_date.txt

	log("STRARTING...................")

	vipyingxiao_page_url = "http://www.vipyingxiao.com/v/weixin.html"

	try:
		# crawling
		vipyingxiao_all_data_list = crawl_single_page(vipyingxiao_page_url)

		# oupput
		output_items_into_file(vipyingxiao_all_data_list, file_path)

	except BaseException as base_error:
		log("error when crawling, cause: %s" % base_error)

	# DONE
	log("ALL DONE!")


if __name__ == '__main__':
	main()