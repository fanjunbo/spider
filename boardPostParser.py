#!/usr/bin/python
#coding=utf-8

import urllib2
import json
import sys
import math
from bs4 import BeautifulSoup
import threading

reload(sys)                   
sys.setdefaultencoding('utf-8')


class Logger:
	def __init__(self):
		self.loggerRoute = {}

	def setRoute(self, name, path, mode):
		if name in self.loggerRoute:
			print 'route exits pls find a new name'
		else:
			stream = open(path, mode)
			self.loggerRoute[name] = { 'path': path, mode: 'mode' , 'stream': stream }
	def trigger (self, name, content):
		if name in self.loggerRoute:
			self.loggerRoute[name]['stream'].write(content + '\n')
		else:
			print 'no such registed path' 



class BoardPostParsor:
	def __init__(self, start, end, workers, timeout):
		self.start = start
		self.end = end
		self.workers = workers
		self.firstRequest = True
		self.timeout = timeout

		Log = Logger()
		Log.setRoute('httpError', './httpError.txt', 'w')
		Log.setRoute('result', './boardsPosts.txt', 'a')
		Log.setRoute('threadLog', './threadLog.txt', 'a')
		self.Logger = Log

	def setHttpRequest(self, timeout):
		self.timeout = timeout

	def generateRanges(self):
		ranges = []
		duration = int((self.end - self.start ) / self.workers)
		for i in range(self.workers):
			ranges.append(self.start + i * duration)
		ranges.append(self.end)
		return sorted(ranges)

	def getHttpRequest(self, url):
		try:
			req = urllib2.Request(url)
			res = urllib2.urlopen(req, timeout=self.timeout)		
			data = json.load(res) 
			html = data['discussions'].replace('\n', '').replace('\r', '')
			totalDiscussionsSoft = int(data['totalDiscussionsSoft'])
			if self.firstRequest:
				self.end = math.ceil(totalDiscussionsSoft / 50)
				print self.end
				self.firstRequest = False
			if html == '':
				return False
			else:
				return html
		except Exception, e:
			self.Logger.trigger('httpError', url)

	def parsePostInfo(self, html):
		res = []
		soup = BeautifulSoup(html, 'html.parser')
		trs = soup.find_all('tr')
		
		for tr in trs:
			vote = str(tr.find('td', class_='voting small').find('div')['data-apollo-up-votes']) \
					+ '/' + str(tr.find('td', class_='voting small').find('div')['data-apollo-down-votes'])
			title = str(tr.find('td', class_='title').find('span', class_='title-span').string)
			link = 'http://boards.na.leagueoflegends.com' + str(tr.find('a', class_='title-link')['href'])
			views = str(tr.find('td', class_='view-counts byline').find('span', class_='number opaque')['data-short-number'])
			replies = str(tr.find('td', class_='num-comments byline').find('span', class_='number opaque')['data-short-number'])
			title = title.strip().replace('#', '')
			timestamp = str(tr.find('td', class_='title').find('span', class_='timeago')['title'].replace('T', ' ').split('.')[0])
			#print timestamp
			res.append({
					'vote': vote, 
					'title': title,
					'link': link,
					'views': views,
					'replies': replies,
					'timestamp': timestamp
				})
		if len(res) > 0:
			return res
		else:
			return False


	def printPostInfo(self, data):
		res = ''
		for item in data:
			new = '{0}#{1}#{2}#{3}#{4}#{5}\n'.format(item['title'], item['link'], item['vote'], item['views'], item['replies'], item['timestamp'])
			res += new
		self.Logger.trigger('result', res)
		# title link vote(upvotes/downvotes) views replies timestamp


	def getThreadProcessInfo(self, pid, current, startIndex, endIndex):
		rate = float(current + 1 - startIndex) / float(endIndex - startIndex)
		return 'pid={0}    {1} out of {2} done. {3}%\n'.format(pid, current + 1 - startIndex, endIndex - startIndex, rate * 100.0)

	def startThread(self, pid, startIndex, endIndex):
		for i in range(startIndex, endIndex):
			url = 'http://boards.na.leagueoflegends.com/api/PEr1qIcT/discussions?sort_type=recent&num_loaded=' + str(i * 50)
			html = self.getHttpRequest(url)
			if not html:
				continue
			data = self.parsePostInfo(html)
			if not data:
				continue
			self.printPostInfo(data)
			logInfo = self.getThreadProcessInfo(pid, i, startIndex, endIndex)
			self.Logger.trigger('threadLog', logInfo)


	def startAll(self):
		threads = []
		ranges = self.generateRanges()
		for i in range(0, len(ranges) - 1):
			threads.append(threading.Thread(target=self.startThread ,args=(i, ranges[i], ranges[i + 1])))
		for t in threads:
			t.start()

if __name__ == '__main__':
	spider = BoardPostParsor(start = 2, end=16921, workers=10, timeout=20)
	spider.startAll()






