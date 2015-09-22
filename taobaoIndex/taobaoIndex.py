#-*- encoding: utf-8 -*-
__author__ = 'XuWeitao'

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import json
from easygui import enterbox

class TaobaoIndexCrawler(object):
	"""
	淘宝指数爬虫类
	"""
	def __init__(self, username, configPath, userConfigPath, webDriver="Firefox"):
		"""
		初始化登录用户名，密码和登录所用的浏览器
		:param username: 用户名
		:param webDriver: 浏览器，默认是火狐浏览器
		"""
		with open(configPath) as CONF:
			self.config     = json.loads( CONF.read() )
		with open( userConfigPath ) as USERCONF:
			#username = username.decode(chardet.detect( username )['encoding']) #解决命令行编码问题
			self.userconfig = json.loads(USERCONF.read())[username]
		self.username   = username
		self.uid        = self.userconfig['uid']
		self.password   = self.userconfig['passwd']
		self.dbname     = self.userconfig["db"]
		self.tableCreateSQL = self.config["tableCreateSQL"]
		self.keyword    = self.userconfig["keyword"]
		self.webDriver  = webDriver

	def login(self, browser):
		"""
		利用配置文件和初始化信息进行模拟登陆
		:param:浏览器对象，已打开原始的登录页面
		:return:浏览器对象
		"""
		browser.get( self.config['taobaoIndexLoginURL'] )
		userNameInput = self.FindElementUntilPresenceByCSS( "#TPL_username_1", browser )
		userNameInput.clear()
		userNameInput.send_keys( self.username+Keys.TAB+self.password+Keys.RETURN )
		loopKey = True
		while loopKey:
			try:
				WebDriverWait( browser, 4 ).until( EC.presence_of_element_located( ( By.CSS_SELECTOR, "#q" ) ) )
				loopKey = False
			except Exception:
				passwordInput  = WebDriverWait(browser,10).until( EC.presence_of_element_located( (By.ID, "TPL_password_1") ) )
				passwordInput.clear()
				passwordInput.send_keys( self.password )
				checkCodeInput = WebDriverWait(browser,10).until( EC.presence_of_element_located( (By.ID,"J_CodeInput_i") ) )
				checkCode = enterbox("请输入验证码(不区分大小写)","验证码输入","", True)
				checkCodeInput.send_keys(checkCode+Keys.RETURN)
				loopKey = True
		return browser

	def getlTrendIndexJSON(self,keyword,browser):
		self.login(browser)
		trendIndexUrl = "http://shu.taobao.com/trendindex.json?query=%s&type=query&from=49&to=0&_=1438164611834"%keyword
		browser.get(trendIndexUrl)
		source = self.FindElementUntilPresenceByCSS("pre",browser)
		return json.loads(source.text)

	def analyzeJsonData(self, jsonData):
		res = jsonData
		res["lastdate"] = time.strftime("%Y-%m-%d",time.localtime(float(unicode(res["lastdate"])[:-3])))
		res["details"] = unicode(res["details"])
		res["provinceNames"] = unicode(res["provinceNames"])
		res["interestNames"] = unicode(res["interestNames"])
		res["totalUser"]     = unicode(res["totalUser"])
		res["queries"]       = unicode(res["queries"])
		res["types"]         = unicode(res["types"])
		column_list = res.keys()
		insertData  = res.values()
		return column_list, insertData

	def crawlIntoMysql(self, MysqlConnect, jsonData):
		columnList,insertData = self.analyzeJsonData(jsonData)
		columns = ",".join(columnList)
		insert  = ",".join([r"%s" for i in range(len(columnList))])
		MysqlConnect.sql = "REPLACE INTO taobaoindex_trendindex(%s) VALUES(%s)"%(columns,insert)
		state = MysqlConnect.update( insertData )
		if not state:
			MysqlConnect.sql = self.tableCreateSQL
			MysqlConnect.update()
			print "created table taobaoindex_trendindex!"
			MysqlConnect.sql = "REPLACE INTO taobaoindex_trendindex(%s) VALUES(%s)"%(columns,insert)
			MysqlConnect.update( insertData )
		print "insert data done!"

	def crawlTrendIndex(self, MysqlConnect, browser ):
		for keyword in self.keyword:
			self.crawlIntoMysql(MysqlConnect, self.getlTrendIndexJSON( keyword, browser ))

	@staticmethod
	def FindElementUntilPresenceByCSS( CSSSelector, browser):
		return WebDriverWait(browser,10).until( EC.presence_of_element_located( (By.CSS_SELECTOR,CSSSelector) ) )