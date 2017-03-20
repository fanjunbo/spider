#!/usr/bin/python
#coding=utf-8

import urllib2
import sys
from bs4 import BeautifulSoup
import threading
import json
import re
from operator import itemgetter

url = 'http://boards.na.leagueoflegends.com/en/c/gameplay-balance/paAkxAB1-just-a-reminder-that-vladimir-has-a-259-winrate-in-lcs-patch-74'
url0 = 'http://boards.na.leagueoflegends.com/en/c/miscellaneous/l3wHwtIl-rewards-for-positive-play?num_loaded=0&parent_id=07ed'

res = urllib2.urlopen(url, timeout=20)
content = res.read().replace('\n', '').replace('\t', '')
content = re.sub( '\s+', ' ', content ).strip()
print '' in content
m = re.findall ( 'document.apolloPageBootstrap.push\((.*?)\); </script>', content, re.DOTALL)
strData = m[0].replace('{ name: \'DiscussionShowPage\', data:' , '')[:-1].replace('false', 'False').replace('true', 'True').replace('null', 'False')
#print type(strData)
strData = eval(strData)
#print strData
file = open('./data.txt', 'w')
file.write(str(strData))
file.close()

file = open('./data.txt', 'r')
for data in file:
	data = eval(data)
	print type(data)
file.close()

res = []
file = open('boardsPosts.txt', 'r')
for line in file:
	if '#' in line:
		res.append(line.split('#'))
res.sort(key=lambda x: x[5])
output = open('boards.txt', 'w')
for item in res:
	output.write('{0}#{1}#{2}#{3}#{4}#{5}'.format(item[0], item[1], item[2], item[3], item[4], item[5]))
output.close()

stat = []
file = open('boards.txt', 'r')
for line in file:
	date = line.split('#')[5].split('-')[0]
	print date
	if date in stat:
		stat += 1
	else:
		stat[date] = 0
for key in stat:
	print key, ' ', stat[key]


# file = open('res.html', 'w')
# file.write(res.read())
# file.close()


# req = urllib2.Request(url0)
# response = urllib2.urlopen(req)
# key = 'For a second there'
# content = response.read().replace('\n', '').replace('\t', '')
# #print content
# print len(content)
# if key in content:
# 	print True