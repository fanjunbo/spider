#!/usr/bin/python
#coding=utf-8

import urllib2
import json
import sys
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
			self.loggerRoute[name]['stream'].write(str(content) + '\n')
		else:
			print 'no such registed path'

CatToKey = {
	'gameplay-balance': '3ErqAdtq',
	'alpha-client-discussion': '2E4zVIwd',
	'story-art': '6kFXY1kR',
	'esports': '9hBQwnEU', 
	'team-recruitment': 'K6EGEal2',
	'skin-champion-concepts': 'A8FQeEA8',
	'mechs-vs-minions': 'AMxvhsRt',
	'player-behavior-moderation': 'ZGEFLEUQ',
	'miscellaneous': 'cIfEodbz',
	'memes': 'Ir7ZrJjF',
	'roleplaying': 'embedly',
	'GD': 'mNBeEEkI',

	'bug-report': 'LqLKtMpN',
	'site-feedback': 'bzRrPGQO',
	'help-support': 'osqw6G4M',
	'developer-corner': 'A7LBtoKc',
	'tips-tricks': 'WEuoGbmp',
	'summoners-rift': 'LFfTlAky',
	'fantasy-lcs': '0d2s1dEp',
	'fancreations': '2XjzURgc',
	'sound-music': 'aAJWt2b9',
	'riot-official': 'Ag8jgd8Q',
	'live-incident-breakdown-na': '6WpmgL9O',
	'live-gameplay': 'NiAR4xXU',
	'champions-skins': 'u1cO6oFT',
	'pentakill': 'NH6ypUrr',
	'breaking-news': False,
	'service-status': False,
	'league-videos': False
}


class boardsPostSpider:
	def __init__(self, workers, srcPath):
		self.url = 'http://boards.na.leagueoflegends.com/api/CAT_KEY/discussions/POST_KEY/comments.json?num_loaded=0&reverse_sort=true&response_format=list&sort_type=recent&page_size=10000&include_pinned=true&sort_field=createdAt&sort_direction=asc&content_type=comment'
		self.timeout = 25
		self.srcPath = srcPath
		self.workers = workers
		Log = Logger()
		Log.setRoute('httpError', './httpError.txt', 'w')
		Log.setRoute('result', './result.txt', 'a')
		Log.setRoute('threadLog', './threadLog.txt', 'a')
		self.Logger = Log

	def httpRequest(self, url):
		try:
			req = urllib2.Request(url)
			res = urllib2.urlopen(req, timeout=20)		
			data = json.load(res)
			comments = data['comments']
			return comments
		except Exception, e:
			self.Logger.trigger('httpError', url)

	def extractRepliesFromComments(self, comments, threadUrl):
		replies = ''
		for comment in comments:
		 	message = comment['message'].replace('#', '').replace('|', '').replace('\n', '').replace('\t', '').replace('\r', '')
		 	upVotes = comment['upVotes'] 
			replies += (message + '|'+ str(upVotes) + '#')
		res = replies + threadUrl
		return res

	def printRepliesToDisk(self, replies):
		self.Logger.trigger('result', replies)

	def generateUrls(self):
		res = []
		for i in range(self.workers):
			res.append([])
		index = 0
		dataInput = open(self.srcPath, 'r')
		for data in dataInput:
			postUrl = data.split('#')[1]
			catName = data.split('#')[1].split('/')[5]
			postKey =  data.split('#')[1].split('/')[6].split('-')[0]
			catKey = CatToKey[catName]
			if not catKey:
				continue
			getUrl = self.url.replace('CAT_KEY', catKey).replace('POST_KEY', postKey)
			res[index].append({'getUrl':getUrl, 'postUrl':postUrl})
			index += 1
			if index >= self.workers:
				index %= self.workers
		print 'tuples generated'
		return res

	def printProcessInfo(self, pid, current, start, end):
		print 'pid={0} {1}/{2} {3}%'.format(pid, current - start, end - start, float(current - start)/(end - start)*100)
	
	def startThread(self, pid, links):
		current = 0
		start = 0
		end = len(links)
		for item in links:
			current += 1
			url = item['getUrl']
			threadUrl = item['postUrl']
			comments = self.httpRequest(url)
			replies = self.extractRepliesFromComments(comments, threadUrl)
			self.printRepliesToDisk(replies)
			self.printProcessInfo(pid, current, start, end)

	def startAll(self):
		links = self.generateUrls()
		threads = []
		for i in range(len(links)):
			threads.append(threading.Thread(target=self.startThread ,args=(i, links[i])))
		for t in threads:
			t.start()


if __name__ == '__main__':
	spider = boardsPostSpider(workers=10, srcPath='./boards.txt')
	spider.startAll()


