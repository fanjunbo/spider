#!/usr/bin/python
#coding=utf-8

import urllib2
import sys
from bs4 import BeautifulSoup
import threading
import MySQLdb



reload(sys)                   
sys.setdefaultencoding('utf-8')



class ThreadParser:
	def __init__(self):
		pass

	def findMaxPageNum(self, soup):
		pages = soup.find('div', 'pager').find_all('a')
		curMaxPageIndex = '0'
		for page in pages:
			curPageIndex = page.string
			if curPageIndex != None and int(curPageIndex) > int(curMaxPageIndex):
				curMaxPageIndex = curPageIndex
		return int(curMaxPageIndex)

	def removeImageIdFromContext(self, context):
		contexts = context.split(' ')
		res = ''
		for element in contexts:
			try:
				int(element)
			except Exception, e:
				res += element + ' '
		return res

	def parseContentFromThread(self, url):
		items = list()
		hasFoundPageNum = False
		page = 1
		maxPageNum = 1
		postStartDate = ''
		while page <= maxPageNum:

			newUrl = url + '&page=' + str(page)
			res = self.getHttpResponse(newUrl)
			if not res:
				return items
			html = res.read().replace('\n', ' ').replace('\r', '').replace('<br>', '.').replace('<br/>', '.')
			soup = BeautifulSoup(html, 'html.parser')
			if page == 1:
				postStartDate = soup.find('div', 'post-header padding-side-10 clearfix').find('span').get_text()
				dates =  postStartDate.split('-')
				postStartDate = '{0}-{1}-{2}'.format(dates[2], dates[1], dates[0])
			if not hasFoundPageNum:
				maxPageNum = self.findMaxPageNum(soup)
				hasFoundPageNum = True
			posts = soup.find_all('div', 'post-message')
			for post in posts:
				if post.div:
					post.div.decompose()
				for ele in post.find_all('p'):
					context = ele.get_text()
					if context == None or context == '':
						continue
					res = self.removeImageIdFromContext(context)
					if res.strip() != '':
						items.append(res.strip())
			page += 1
		res = ''
		for sen in items:
			sen = sen.replace('#', '').strip().replace(',', ';')
			res += sen + '#'
		return res + ',' + postStartDate

	def getHttpResponse (self, url):
		try:
			res = urllib2.urlopen(url, timeout=20)
			return res
		except urllib2.URLError, e:
			error = open('./error.log', 'a')
			error.write('[ERROR] ' + e.reason + ' ' + url + '\n')
			error.close()
			return False





class ForumSpider:
	def __init__(self, start, end, workers):
		self.start = start
		self.end = end
		self.workers = workers

	def setMySQL(self, host, user, passwd, schema, dbLogPath):
		self.host = host
		self.user = user
		self.passwd = passwd
		self.schema = schema
		self.dbLogPath = dbLogPath

	def setHttpRequest(self, timeout, httpLogPath):
		self.timeout = timeout
		self.httpLogPath = httpLogPath

	def setBaseURL(self, url):
		self.baseURL = url

	def getHttpResponse(self, fullURL):
		try:
			res = urllib2.urlopen(fullURL, timeout=self.timeout)
			return res
		except Exception, e:
			error = open('./error.log', 'a')
			error.write('[ERROR] ' + e.reason + ' ' + url + '\n')
			error.close()
			return False

	def openMySQL(self):
		return MySQLdb.connect(host=self.host, user=self.user, passwd=self.passwd, db=self.schema)

	def extractDataFromHTML(self, html):
		items = []
		html = html.replace('\n', ' ').replace('\r', '')
		soup = BeautifulSoup(html, 'html.parser')
		trs = soup.find_all('tbody')[0].find_all('tr')
		
		for tr in trs:
			for string in tr.find('a').stripped_strings:
				if str(string):
					thread = str(string).replace(',', ';').strip() 
			link = 'http://forums.na.leagueoflegends.com/' + str(tr.find('a')['href'])
			postId = str(tr.find('a')['href']).split('t=')[1].strip()
			replies = str(tr.find('td', class_='replies').find('span').string).strip()
			views = str(tr.find('td', class_='views').string).strip()
			if postId == '4909234' or postId == '4813730':
				continue
			items.append({
				'title': thread,
				'link': link,
				'replies': replies,
				'views': views,
				'id': postId
			})
		return items

	def writeForumsToMySQL(self, db, items): 
		cur = db.cursor()
		for item in items:
			res = '"' + item['id'] + '","' + item['title'] + '","' + item['link'] + '","' + item['replies'] + '","' + item['views'] + '","' + 'NULL"'
			try:
				cur.execute('insert into postList values (' + res + ')')
			except Exception, e:
				self.printToFile(self.dbLogPath, str(e) + ' ' + res, 'a')
				continue
		db.commit()

	def generateRanges(self):
		ranges = []
		duration = int((self.end - self.start ) / self.workers)
		for i in range(self.workers):
			ranges.append(self.start + i * duration)
		ranges.append(self.end)
		return sorted(ranges)

	def setOutputStream(self, fout):
		if fout:
			self.fout = fout

	def startThread(self, pid, start, end, db):
		postParser = ThreadParser()
		for i in range(start, end):
			fullURL = self.baseURL + '&page=' + str(i)
			print fullURL + '[{0}%]'.format(str((i - start) / (end - start) * 100))
			res = self.getHttpResponse(fullURL)
			if res:
				html = res.read()
				items = self.extractDataFromHTML(html)

				for data in items:
					contents = postParser.parseContentFromThread(data['link'])
					try:
						self.fout.write(data['title'] + ',' + data['link'] + ','  + contents + ','  + data['replies'] +',' + data['views'] + '\n')
					except Exception, e:
						print 'write error'
				#self.writeForumsToMySQL(db, items)


	def startAll(self):
		threads = []
		ranges = self.generateRanges()
		for i in range(0, len(ranges) - 1):
			#db = self.openMySQL()
			db = ''
			threads.append(threading.Thread(target=self.startThread ,args=(i, ranges[i], ranges[i + 1], db)))
		for t in threads:
			t.start()



if __name__ == '__main__': 
	fout = open('./result.csv', 'a')
	spider = ForumSpider(start = 3, end=70000, workers=30)
	spider.setMySQL(host='localhost',  user='root', passwd='root', schema='forums', dbLogPath='./dbError.log')
	spider.setHttpRequest(timeout = 20, httpLogPath = './httpRequest.log')
	spider.setBaseURL('http://forums.na.leagueoflegends.com/board/forumdisplay.php?f=2')
	spider.setOutputStream(fout)

	spider.startAll()

