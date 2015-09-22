#-*- coding: utf-8 -*-

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import xlrd
import json
import os
import datetime
from easygui import enterbox
import sys
import requests

class BusinessStaffCrawler(object):
	"""
	生意参谋爬虫类
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
		self.webDriver  = webDriver

	def login(self, browser):
		"""
		利用配置文件和初始化信息进行模拟登陆
		:param:浏览器对象，已打开原始的登录页面
		:return:浏览器对象
		"""
		browser.get( self.config['BussinessStaffURL'] )
		browser.switch_to.frame( browser.find_element_by_tag_name("iframe") )
		userNameInput = browser.find_element_by_name("TPL_username")
		userNameInput.clear()
		userNameInput.send_keys( self.username+Keys.TAB+self.password+Keys.RETURN )
		browser.switch_to.default_content()
		loopKey = True
		while loopKey:
			try:
				WebDriverWait( browser, 4 ).until( EC.presence_of_element_located( ( By.CSS_SELECTOR, "ul>li>a>div>strong>span" ) ) )
				loopKey = False
			except Exception:
				browser.switch_to.frame( browser.find_element_by_tag_name("iframe") )
				passwordInput  = WebDriverWait(browser,10).until( EC.presence_of_element_located( (By.ID, "TPL_password_1") ) )
				passwordInput.clear()
				passwordInput.send_keys( self.password )
				checkCodeInput = WebDriverWait(browser,10).until( EC.presence_of_element_located( (By.ID,"J_CodeInput_i") ) )
				checkCode = enterbox("请输入验证码(不区分大小写)","验证码输入","", True)
				checkCodeInput.send_keys(checkCode+Keys.RETURN)
				browser.switch_to.default_content()
				loopKey = True

		return browser

	def __strPercentClean(self, string):
		return float( string.rstrip("%") ) / 100 if string.endswith("%") else string

	def crawlRawFactShopData(self, filePathAndName):
		"""
		从下载的RawFactShopData里爬取具体数据
		:param filePathAndName:文件完整的绝对路径
		:return:返回可以执行数据库批量插入函数的列表
		"""
		try:
			excelData = xlrd.open_workbook(filePathAndName )
		except Exception,e:
			print "file error:",e
			return []
		table = excelData.sheets()[0]

		insertData = list()
		for rowNumber in xrange( 4, table.nrows ):
			rowInsertTemp = list()
			rowDataList   = table.row_values(rowNumber)
			rowInsertTemp.append( rowDataList[0] )
			rowInsertTemp.append( self.uid )
			for item in rowDataList[1:]:
				rowInsertTemp.append( float( self.__strPercentClean(unicode(item).replace(",","")) if item != "-" and item != "" else 0.0 ) )

			insertData.append( tuple( rowInsertTemp ) )

		return insertData



	def closePreview(self, browser):
		self.FindElementUntilPresenceByCSS(".show > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > button:nth-child(1)",browser).click()
		return browser

	def clickThematicTools(self, browser):
		self.FindElementUntilPresenceByCSS("li.product:nth-child(5) > a:nth-child(1)", browser).click()
		return browser

	def clickItemAnalysis(self, browser):
		self.FindElementUntilPresenceByCSS(".current > a:nth-child(2) > span:nth-child(1)", browser).click()
		return browser

	def clickSalesAnalysis(self, browser):
		self.FindElementUntilPresenceByCSS("li.active:nth-child(2) > a:nth-child(1)",browser).click()
		return browser

	def downloadFile(self, url, downloadFileName, browser):
		"""
		下载文件函数
		:param url:下载的链接
		:param downloadFileName:下载的文件名
		:param browser:浏览器对象
		:return:返回下载成功失败的布尔值
		"""
		try:
			cookies  = { item['name']:item['value'] for item in browser.get_cookies() }
			response = requests.get( url=url, cookies=cookies )
			with open(unicode(self.userconfig['downloadPath'])+u"\\"+unicode(downloadFileName),"wb") as downloadedFile:
				downloadedFile.write(response.content)
			return True
		except Exception,e:
			print e
			sys.stdout.flush()
			return False

	def crawlExcelShopItemSum(self, itemid, filePathAndName, filename, fileid):
		"""
		从下载的excel表格中获取raw_fact_item_sum的数据
		:param itemid:商品的id编号
		:param nameDateStart:下载excel表格对应的起始时间
		:param nameDateEnd:下载excel表格对应的结束时间
		:param fileid:数据库中的id和joinid字段，表示相同文件名的文件id
		:return:返回可以通过updateMany方法直接写入数据库的元组列表
		"""

		try:
			excelData = xlrd.open_workbook(filePathAndName )
		except Exception,e:
			print "file error:",e
			return []
		table = excelData.sheets()[0]

		insertData = list()
		for rowNumber in xrange( 4, table.nrows ):
			rowInsertTemp = list()
			rowDataList   = table.row_values(rowNumber)
			rowInsertTemp.append( rowDataList[0] )
			rowInsertTemp.append( self.uid )
			rowInsertTemp.append( itemid )
			rowInsertTemp.append(rowDataList[1])
			for item in rowDataList[2:]:
				rowInsertTemp.append( float( self.__strPercentClean(unicode(item).replace(",","")) if item != "-" and item != "" else 0.0 ) )

			rowInsertTemp.append( fileid ) #id字段
			rowInsertTemp.append( fileid ) #jion_id字段
			rowInsertTemp.append( filename ) #short_filename字段
			rowInsertTemp.append( self.getTimeStamp() ) #
			insertData.append( tuple( rowInsertTemp ) )

		return insertData

	def crawlExcelShopItemKeyword(self,itemid, filePathAndName, filename, fileid, Date):
		"""
		从下载的excel表格中获取raw_fact_item_keyword的数据
		:param itemid:商品的id编号
		:param nameDateStart:下载excel表格对应的起始时间
		:param nameDateEnd:下载excel表格对应的结束时间
		:param fileid:数据库中的id和joinid字段，表示相同文件名的文件id
		:return:返回可以通过updateMany方法直接写入数据库的元组列表
		"""


		try:
			excelData = xlrd.open_workbook(filePathAndName )
		except Exception,e:
			print "file error:",e
			return []
		table      = excelData.sheets()[0]
		insertData = list()
		for rowNumber in xrange( 5, table.nrows ):
			rowInsertTemp = list()
			rowDataList   = table.row_values(rowNumber)
			rowInsertTemp.append( Date )
			rowInsertTemp.append( self.uid )
			rowInsertTemp.append( itemid )
			rowInsertTemp.append(rowDataList[0])
			for item in rowDataList[1:]:
				rowInsertTemp.append( float( self.__strPercentClean(unicode(item)) if item != "-" and item != "" else 0.0 ) )
			rowInsertTemp.append( fileid ) #id字段
			rowInsertTemp.append( fileid ) #join_id字段
			rowInsertTemp.append( filename ) #short_filename字段
			rowInsertTemp.append( self.getTimeStamp() )
			insertData.append( tuple( rowInsertTemp ) )

		return insertData

	def crawlExcelShopItemUVSrc(self, itemid, filePathAndName, filename, fileid, deviceid, Date):
		"""
		从下载的excel表格中获取raw_fact_item_uvsrc的数据
		:param itemid:商品的id编号
		:param nameDateStart:下载excel表格对应的起始时间
		:param nameDateEnd:下载excel表格对应的结束时间
		:param fileid:数据库中的id和joinid字段，表示相同文件名的文件id
		:param deviceid:1表示PC端，2表示无线端
		:return:返回可以通过updateMany方法直接写入数据库的元组列表
		"""
		try:
			excelData = xlrd.open_workbook(filePathAndName )
		except Exception,e:
			print "file error:",e
			return []
		table = excelData.sheets()[0]

		insertData = list()
		for rowNumber in xrange( 5, table.nrows ):
			rowInsertTemp = list()
			rowDataList   = table.row_values(rowNumber)
			rowInsertTemp.append( Date )
			rowInsertTemp.append( self.uid )
			rowInsertTemp.append( itemid )
			rowInsertTemp.append( rowDataList[0] )
			rowInsertTemp.append( u"PC端" if deviceid == 1 else u"无线端" )
			for item in rowDataList[1:]:
				rowInsertTemp.append( float( self.__strPercentClean(unicode(item)) if item != "-" and item != "" else 0.0 ) )
			rowInsertTemp.append( fileid ) #id字段
			rowInsertTemp.append( fileid ) #jion_id字段
			rowInsertTemp.append( filename ) #short_filename字段
			rowInsertTemp.append( self.getTimeStamp() ) #
			insertData.append( tuple( rowInsertTemp ) )

		return insertData

	def crawlExcelFactIndKeywordUV(self, catid, filePathAndName, filename, fileid, deviceid, Date):
		"""

		:param itemid:
		:param filePathAndName:
		:param filename:
		:param fileid:
		:param deviceid:
		:param Date:
		:return:
		"""
		try:
			excelData = xlrd.open_workbook(filePathAndName )
		except Exception,e:
			print "file error:",e
			return []
		table = excelData.sheets()[0]

		insertData = list()
		for rowNumber in xrange( 4, table.nrows ):
			rowInsertTemp = list()
			rowDataList   = table.row_values(rowNumber)
			rowInsertTemp.append( Date )
			rowInsertTemp.append( u"PC端" if deviceid == 1 else u"无线端" )
			rowInsertTemp.append( catid )
			rowInsertTemp.append( rowDataList[0] )
			for item in rowDataList[1:]:
				rowInsertTemp.append( float( self.__strPercentClean(unicode(item).replace(",","")) if item != "-" and item != "" else 0.0 ) )
			rowInsertTemp.append( fileid ) #id字段
			rowInsertTemp.append( fileid ) #jion_id字段
			rowInsertTemp.append( filename ) #short_filename字段
			rowInsertTemp.append( self.getTimeStamp() ) #
			insertData.append( tuple( rowInsertTemp ) )

		return insertData

	def crawlRawFactShopDataToMySQL(self, browser, MySQLConnect):
		"""
		登录进去之后到自助取数页面开始爬取所有的raw_fact_shop数据表数据。4张表
		:param browser:浏览器对象
		:param MySQLConnect:数据库连接对象
		:return:True执行完毕，False执行失败
		"""
		try:
			downloadFileNameAndLinks = self.getAllRawFactDownloadLinks( MySQLConnect )
			for NameAndLink in downloadFileNameAndLinks:
				#[0]url,[1]tag
				url      = NameAndLink[0]
				fileName = NameAndLink[1]
				fileFullName = unicode(self.userconfig['downloadPath'])+u"\\"+unicode(fileName)
				self.downloadFile( url, fileName, browser )
				indertData = self.crawlRawFactShopData( fileFullName )
				if "od" in fileName:
					MySQLConnect.sql = "REPLACE INTO raw_fact_shop_order_sum VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s," \
			          " %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )"
					MySQLConnect.updateMany(indertData)
					os.remove( fileFullName )
					print "done raw_fact_shop_order_sum!"
					sys.stdout.flush()
				elif "uv" in fileName:
					MySQLConnect.sql = "REPLACE INTO raw_fact_shop_uv VALUES( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )"
					MySQLConnect.updateMany(indertData)
					os.remove( fileFullName )
					print "done raw_fact_shop_uv!"
					sys.stdout.flush()
				elif "mk" in fileName:
					MySQLConnect.sql = "REPLACE INTO raw_fact_shop_collect VALUES ( %s, %s, %s, %s, %s, %s )"
					MySQLConnect.updateMany(indertData)
					os.remove( fileFullName )
					print "done raw_fact_shop_collect!"
					sys.stdout.flush()
				elif "srv" in fileName:
					MySQLConnect.sql = "REPLACE INTO raw_fact_shop_dsr VALUES( %s, %s, %s, %s, %s, %s, %s, %s, %s )"
					MySQLConnect.updateMany(indertData)
					os.remove( fileFullName )
					print "done raw_fact_shop_dsr!"
					sys.stdout.flush()
				else:
					print "###############################################"
					print "Unexpected Tag!"
					sys.stdout.flush()
					print "###############################################"
					continue
		except Exception,e:
			return False
		else:
			return True

	def crawlRawFactShopItemDataToMySQL(self, browser, MySQLConnect, initial=0):
		"""
		登录进去之后开始爬取所有的raw_fact_shop_item数据表数据。3张表
		:param browser:浏览器对象
		:param MySQLConnect:数据库连接对象
		:return:True执行完毕，False执行失败
		"""
		try:
			MySQLConnect.sql = "SELECT DISTINCT auction_id FROM dim_auction WHERE seller_id = %d ORDER BY recent_sold_quantity DESC limit 100"%self.uid
			auctionList = MySQLConnect.query(0)


			order_rule = 'expose'

			if initial == 1:
				uvsrcDayRange   = 32
				keywordDayRange = 8
				start = getDate(32)
				end   = getDate(1)
			else:
				start = getDate(8)
				end   = getDate(1)
				uvsrcDayRange = keywordDayRange = 2

			for fileid, auction in enumerate(auctionList):
				auctionid = auction[0]
				#下载excel表方式获取raw_fact_shop_item_sum的数据
				url = 'http://bda.sycm.taobao.com/download/excel/items/itemanaly/ItemTrendExcel.do?dateRange=' \
				      +start+'|'+end+'&dateType=range&itemId='+unicode(auctionid)+'&device=1'

				fileFullPath = unicode(self.userconfig['downloadPath']) + u'\\' + u'【生意参谋】单品分析-趋势分析-%s-%s.xls'%(start,end)
				fileName =  u'【生意参谋】单品分析-趋势分析-%s-%s.xls'%(start,end)

				if self.downloadFile( url, fileName, browser ):
					insertData = self.crawlExcelShopItemSum( auctionid, fileFullPath, fileName, fileid )
					print "done download raw_fact_shop_item_sum:" + unicode(auctionid)
					sys.stdout.flush()
					if len(insertData)==0:
						os.remove(fileFullPath)
						print u"data empty!"+ unicode(auctionid)
						sys.stdout.flush()
						continue


					os.remove( fileFullPath )
					MySQLConnect.sql = "REPLACE INTO raw_fact_shop_item_sum VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s," \
					      " %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )"
					MySQLConnect.updateMany( insertData )

					print "done write into raw_fact_shop_item_sum"
					sys.stdout.flush()
				else:
					print "cannot download a valid raw_fact_shop_item_sum file!auctionid = "+unicode( auctionid )
					sys.stdout.flush()

				# 下载excel表方式获取raw_fact_shop_item_keyword的数据
				# 逐个日期执行
				for deltaDay in xrange( 1, keywordDayRange ):
					excelDate = getDate( deltaDay )
					url = 'http://bda.sycm.taobao.com/download/excel/items/itemanaly/ItemKeywordAnalysisExcel.do?device=1&itemId=' + unicode(
						auctionid ) + '&dateRange=' + excelDate + '|' + excelDate + '&dateType=recent1&order=' + order_rule + '&orderType=asc&search=&searchType=taobao'
					fileFullPath = unicode(self.userconfig['downloadPath']) + u'\\' + u'【生意参谋平台】PC商品关键词效果分析%s_%s.xls'%(excelDate,excelDate)
					fileName =  u'【生意参谋平台】PC商品关键词效果分析%s_%s.xls'%(excelDate,excelDate)

					if self.downloadFile( url, fileName, browser ):
						#其中deltaDay-i就是文件的id号
						insertData = self.crawlExcelShopItemKeyword( auctionid, fileFullPath, fileName, deltaDay - 1, excelDate )
						print "done download raw_fact_shop_item_keyword:" + unicode(auctionid) + ',' + excelDate
						sys.stdout.flush()
						if len(insertData)==0:
							os.remove(fileFullPath)
							print u"data empty!"+ unicode(auctionid)  + ',' + excelDate
							sys.stdout.flush()
							continue
						os.remove(fileFullPath)
						MySQLConnect.sql = "REPLACE INTO raw_fact_shop_item_keyword VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
						MySQLConnect.updateMany(insertData)
						print "done write into raw_fact_shop_item_keyword"
						sys.stdout.flush()
					else:
						print "cannot download a valid raw_fact_shop_item_keyword file!auctionid = "+unicode( auctionid ) + ',' + excelDate
						sys.stdout.flush()

				# 下载excel表方式获取raw_fact_shop_uvsrc的数据
				for deltaDay in xrange( 1, uvsrcDayRange ):
					excelDate = getDate( deltaDay )
					for deviceID in (1,2):
						#1:PC端，2:无线端
						url = 'http://bda.sycm.taobao.com/download/excel/items/itemanaly/ItemLev1FromToExcel.do?device=' + unicode(
							deviceID ) + '&itemId=' + unicode( auctionid ) + '&dateRange=' + excelDate + '|' + excelDate + '&dateType=day&reqIndex=uv'
						if deviceID == 1:
							fileFullPath = unicode(self.userconfig['downloadPath']) + u'\\' + u'【生意参谋平台】pc端商品来源去向一级来源%s_%s.xls'%(excelDate,excelDate)
							fileName =  u'【生意参谋平台】pc端商品来源去向一级来源%s_%s.xls'%(excelDate,excelDate)
						else:#deviceid == 2
							fileFullPath = unicode(self.userconfig['downloadPath']) + u'\\' + u'【生意参谋平台】无线端商品来源去向一级来源%s_%s.xls'%(excelDate,excelDate)
							fileName =  u'【生意参谋平台】无线端商品来源去向一级来源%s_%s.xls'%(excelDate,excelDate)
						if self.downloadFile(url, fileName, browser):
							insertData = self.crawlExcelShopItemUVSrc(auctionid,fileFullPath,fileName,deltaDay - 1,deviceID, excelDate)
							print "done download raw_fact_shop_item_uvsrc:" + unicode(auctionid) + ',' + excelDate
							sys.stdout.flush()
							if len(insertData)==0:
								os.remove(fileFullPath)
								print u"data empty!"+ unicode(auctionid)  + ',' + excelDate
								sys.stdout.flush()
								continue
							MySQLConnect.sql = "REPLACE INTO raw_fact_shop_item_uvsrc VALUES( %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s )"
							MySQLConnect.updateMany(insertData)
							os.remove(fileFullPath)
							print "done write into raw_fact_shop_item_uvsrc!"
							sys.stdout.flush()
						else:
							print "cannot download a valid raw_fact_shop_item_uvsrc file!auctionid = "+unicode( auctionid ) + ',' + excelDate
							sys.stdout.flush()

		except Exception,e:
			print e
			sys.stdout.flush()
		else:
			return True

	def crawlFactIndKeywordUVDataToMySQL(self, browser, MySQLConnect, initial=0):
		try:
			MySQLConnect.sql = "SELECT cat_id FROM etc_cat_keyword" \
			                   " ORDER BY id asc"
			catList = MySQLConnect.query(0)

			if initial == 1:
				uvsrcDayRange   = 32
			else:
				uvsrcDayRange   = 2
			MySQLConnect.sql = "REPLACE INTO fact_ind_keyword_uv VALUES( %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s )"
			for cat_id in catList:
				for deltaDay in xrange( 1, uvsrcDayRange ):
					excelDate = getDate( deltaDay )
					for devid in( 1, 2 ):
						url = 'http://sycm.taobao.com/excel/IndustryKeywordExcel.do?device='+str(devid)+'&cateId='+str(cat_id[0])\
						      +'&pageSize=100&orderBy=hotIndex&desc=&date=1&page=1&sycmToken='+str(self.userconfig['token'])+'&isHot=true'
						if devid == 1:
							fileFullPath = unicode(self.userconfig['downloadPath']) + u'\\' + u'【生意参谋】行业排行-搜索词排行榜-%s_%s_pc.xls'%(excelDate,excelDate)
							fileName =  u'【生意参谋】行业排行-搜索词排行榜-%s_%s_pc.xls'%(excelDate,excelDate)
						else:#deviceid == 2
							fileFullPath = unicode(self.userconfig['downloadPath']) + u'\\' + u'【生意参谋】行业排行-搜索词排行榜-%s_%s_wireless.xls'%(excelDate,excelDate)
							fileName =  u'【生意参谋】行业排行-搜索词排行榜-%s_%s_wireless.xls'%(excelDate,excelDate)
						if self.downloadFile(url, fileName, browser):
							insertData = self.crawlExcelFactIndKeywordUV(cat_id[0],fileFullPath,fileName, devid, deltaDay - 1, excelDate)
							if len(insertData)==0:
								os.remove(fileFullPath)
								print u"data empty!"+ unicode(cat_id[0]) + ',' + excelDate
								sys.stdout.flush()
								continue
							print "done download fact_ind_keyword_uv:" + unicode(cat_id[0]) + ',' + excelDate
							sys.stdout.flush()
							try:
								MySQLConnect.updateMany(insertData)
							except Exception,e:
								print e
								sys.stdout.flush()
								MySQLConnect.sql = "REPLACE INTO fact_ind_keyword_uv VALUES( %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'' )"
								MySQLConnect.updateMany(insertData)
							os.remove(fileFullPath)
							print "done write into fact_ind_keyword_uv!"
							sys.stdout.flush()
						else:
							print "cannot download a valid fact_ind_keyword_uv file!catid = "+unicode( cat_id[0] ) + ',' + excelDate
							sys.stdout.flush()


		except Exception,e:
			print e
			sys.stdout.flush()

	def crawlRawFactDataToMySQL(self, browser, MySQLConnect, initial=0):
		try:
			self.login(browser)
			#self.FindElementUntilPresenceByCSS("li.product:nth-child(4) > a:nth-child(1)", browser).click()
			self.crawlRawFactShopDataToMySQL( browser, MySQLConnect )
			self.crawlRawFactShopItemDataToMySQL( browser, MySQLConnect, initial )
			self.crawlFactIndKeywordUVDataToMySQL( browser, MySQLConnect, initial )
		except Exception,e:
			print e
			sys.stdout.flush()
		else:
			return True


	@staticmethod
	def FindElementUntilPresenceByCSS( CSSSelector, browser):
		return WebDriverWait(browser,10).until( EC.presence_of_element_located( (By.CSS_SELECTOR,CSSSelector) ) )

	@staticmethod
	def FindAllElementsUntilPresenceByCSS( CSSSelector, browser):
		return WebDriverWait(browser,10).until( EC.presence_of_all_elements_located( ( By.CSS_SELECTOR, CSSSelector ) ) )

	@staticmethod
	def getTimeStamp():
		return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	@staticmethod
	def getAllRawFactDownloadLinks( MySQLConnect ):
		"""获取四张我要取数中的报表在数据库中存储的url和tag(文件名)"""
		MySQLConnect.sql = "SELECT distinct url, tag FROM etc_download_sycm"
		return MySQLConnect.query(0)

def getDate(delta_days=0):
	date = (datetime.datetime.now()-datetime.timedelta(delta_days)).strftime("%Y-%m-%d")
	return date

if __name__ == "__main__":
	pass
	# Raw     = Mysql.RawMysql()
	# BSC     = BusinessStaffCrawler( username=u"小鳄龟的春天:春风入夜",
	#                                configPath=r"E:\xuweitao\WebSpider\taobao\configure.json",
	#                                userConfigPath=r"E:\xuweitao\WebSpider\taobao\userConfigure.json")
	# #注意此处的profiles是Administor的profile，如果执行脚本的权限不够会出发shutil.Error，找不到文件的错误
	# #if BSC.webDriver == "Firefox":
	# firefoxProfile = webdriver.FirefoxProfile(BSC.config['firefoxProfile'] )
	# binary  = FirefoxBinary( BSC.config['webDriverPath']['Firefox'] )
	# #不加载profile启动的Firefox将是一个全新的,不安装任何Add-On的Firefox.因此插件无法使用，所以需要制定profile
	# BROWSER = webdriver.Firefox(firefox_binary=binary, firefox_profile=firefoxProfile)
	#
	#
	# BSC.crawlRawFactDataToMySQL( BROWSER, Raw )
	# #time.sleep(3)
	# #BROWSER.get( "http://shu.taobao.com/trendindex.json?query=%E6%B8%AF%E5%B8%81&type=query&from=49&to=0&_=1438164611834&qq-pf-to=pcqq.c2c" )
	# #JSON2Crawl = BSC.FindElementUntilPresenceByCSS("body>pre", BROWSER).text
	# #with open( r"e:\\xuweitao\WebSpider\\taobao\\test.json", "w" ) as ftest:
	# #	ftest.write( JSON2Crawl.encode("utf8") )
	#
	# BROWSER.close()











