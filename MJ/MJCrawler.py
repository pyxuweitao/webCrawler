# -*- encoding: utf-8 -*-
__author__ = 'XuWeitao'
import time
import json
import requests
import copy
import subprocess
import datetime
import multiprocessing



class MjCrawler(object):

	def __init__(self, headers=None, loginData=None, loginUrl=None, proxy=None):
		self.headers = headers if headers is not None else {"Host": "www.maijia.com",
		                                                    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0",
		                                                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
		                                                    "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
		                                                    "Accept-Encoding": "gzip,deflate",
		                                                    "Connection": "keep-alive"}
		self.loginData = loginData if loginData is not None else {"redirectURL":"http://www.maijia.com/",
		                                                          "location":"main",
		                                                          "loginCode":"",
		                                                          "loginPassword":""}
		self.loginUrl = loginUrl if loginUrl is not None else "http://login.maijia.com/?redirectURL=http%3A%2F%2Fwww.maijia.com%2F"
		self.cookies  = dict()
		self.proxy    = {"http":"http://202.194.101.150:80"} if proxy is None else proxy

	def login(self, loginScriptPath, url=None, username=None, passwd=None):
		"""
		卖家网登陆
		:param loginScriptPath:登录的phantomjs脚本的绝对路径
		:param url:登陆的url
		:param username:登陆用户名
		:param passwd:登陆密码
		:return:
		"""
		if username is not None and passwd is not None:
			self.loginData['loginCode']     = username
			self.loginData['loginPassword'] = passwd
		if url is not None:
			self.loginUrl = url

		cmd     = 'phantomjs %s %s %s %s' %( loginScriptPath, self.loginUrl, username, passwd )
		proc    = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
		for row in proc.stdout.readlines():
			self.cookies[row.split('=')[0]] = row.split('=')[1].rstrip('\r\n')

		print username+":login Successfully!"


	def get_per_page_of_data_industry_hotitems_list(self, url, params, pageno, itemList, itemIDList, GET_PER_PAGE_OF_DATA_INDUSTRY_HOTITEMS_LIST_STOP_FLAG ):
		params["pageNo"] = pageno
		response         = requests.get(url,params="&".join(["%s=%s"%(k,v) for k,v in params.items()]),headers=self.headers, cookies=self.cookies, proxies=self.proxy)
		print response.url
		jsonData         = json.loads(response.content)
		if len(jsonData["data"]["list"])==0:#到了没有数据的页码
			GET_PER_PAGE_OF_DATA_INDUSTRY_HOTITEMS_LIST_STOP_FLAG.value = 1
		else:
			rawData = jsonData["data"]["list"]
			if len(rawData) != 0:
				for item in rawData:
					itemList.append( item )
					itemIDList.append( item['id'] )

	def get_data_industry_hotitems_list(self, userConfig, MysqlConnect):
		try:
			serverProcess = multiprocessing.Manager()
			GET_PER_PAGE_OF_DATA_INDUSTRY_HOTITEMS_LIST_STOP_FLAG = serverProcess.Value("i",0)
			apiConfig = userConfig["APIConfig"]['data_industry_hotitems_list']
			if len(apiConfig["params"]["cid"]) == 0:
				MysqlConnect.sql           = "SELECT DISTINCT cat_id FROM dim_itemcat"
				MysqlConnect.reConnect()
				catidList                  = MysqlConnect.query(0)
				apiConfig["params"]["cid"] = [catid[0] for catid in catidList]
			itemList   = serverProcess.list()
			itemIDList = serverProcess.list()
			paramsReal = copy.deepcopy( apiConfig["params"] )

			if len(apiConfig["params"]["cid"] ) != 0:
				for catid in apiConfig["params"]["cid"]:
					GET_PER_PAGE_OF_DATA_INDUSTRY_HOTITEMS_LIST_STOP_FLAG.value = 0
					paramsReal["cid"] = catid
					if len(apiConfig["params"]["pageNo"]) == 0:
						pageno = 1
						pageStage = 20 #每次并发爬取多少页
						while GET_PER_PAGE_OF_DATA_INDUSTRY_HOTITEMS_LIST_STOP_FLAG.value != 1:
							jobs = list()
							for i in range(pageno, pageno+pageStage):
								p = multiprocessing.Process( target=self.get_per_page_of_data_industry_hotitems_list, args=(apiConfig["url"],paramsReal, i, itemList, itemIDList, GET_PER_PAGE_OF_DATA_INDUSTRY_HOTITEMS_LIST_STOP_FLAG,) )
								p.start()
								jobs.append(p)
							for p in jobs:
								p.join()
							pageno += pageStage
					else:
						for pageno in apiConfig["params"]["pageNo"]:
							paramsReal["pageNo"] = pageno
							response  = requests.get( apiConfig['url'], params="&".join(["%s=%s"%(k,v) for k,v in paramsReal.items()]), headers=self.headers,cookies=self.cookies, proxies=self.proxy  )
							print response.url
							jsonData = json.loads(response.content)
							if len(jsonData["data"]["list"])==0:#到了没有数据的页码
								break
							else:
								rawData = jsonData["data"]["list"]
								if len(rawData) != 0:
									for item in rawData:
										itemList.append(item)
										itemIDList.append(item['id'])
			else:
				print "get_data_industry_hotitems_list:data empty!"
			return itemList,itemIDList
		except Exception,e:
			print "ERROR:>get_data_industry_hotitems_list:",e



	def crawl_data_industry_general_trend(self, userConfig, MysqlConnect, dbConfig):
		try:
			apiConfig = userConfig["APIConfig"]['data_industry_general_trend']
			if len(apiConfig["params"]["cid"]) == 0:
				MysqlConnect.sql           = "SELECT DISTINCT cat_id FROM dim_itemcat"
				MysqlConnect.reConnect()
				catidList                  = MysqlConnect.query(0)
				apiConfig["params"]["cid"] = [catid[0] for catid in catidList]
			tableName  = apiConfig["tableName"]
			columnList = apiConfig["columnList"]
			rawInsertData = list()
			paramsReal    = copy.deepcopy( apiConfig["params"] )
			if len(apiConfig["params"]["cid"] ) != 0:
				for catid in apiConfig["params"]["cid"]:
					paramsReal["cid"] = catid
					response = requests.get( apiConfig['url'], params="&".join(["%s=%s"%(k,v) for k,v in paramsReal.items()]), headers=self.headers,cookies=self.cookies, proxies=self.proxy  )
					rawData  = json.loads(response.content)['data']
					for row in rawData:
						row['cat_id'] = catid
						row['date'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime( float(unicode(row['date'])[:-3]) ))
						rawInsertData.append( [row[k] for k in columnList ] )

				self.crawlToMysql( columnList, rawInsertData, MysqlConnect, tableName, dbConfig )
			else:
				print "crawl_data_industry_general_trend:data empty!"
		except Exception,e:
			print "ERROR:>crawl_data_industry_general_trend:",e

	def crawl_data_industry_hotshops_list(self, userConfig, MysqlConnect, dbConfig):
		#rawInsertData = self.crawlAPI( url, params, MysqlConnect )
		try:
			apiConfig = userConfig["APIConfig"]['data_industry_hotshops_list']
			if len(apiConfig["params"]["cid"]) == 0:
				MysqlConnect.sql           = "SELECT DISTINCT cat_id FROM dim_itemcat"
				MysqlConnect.reConnect()
				catidList                  = MysqlConnect.query(0)
				apiConfig["params"]["cid"] = [catid[0] for catid in catidList]
			tableName  = apiConfig["tableName"]
			columnList = apiConfig["columnList"]
			rawInsertData = list()
			paramsReal    = copy.deepcopy( apiConfig["params"] )

			if len(apiConfig["params"]["cid"] ) != 0:
				for catid in apiConfig["params"]["cid"]:
					rawData           = list()
					paramsReal["cid"] = catid
					if len(apiConfig["params"]["pageNo"]) == 0:
						pageno = 1
						while True:
							paramsReal["pageNo"] = pageno
							response  = requests.get( apiConfig['url'], params="&".join(["%s=%s"%(k,v) for k,v in paramsReal.items()]),headers=self.headers, cookies=self.cookies, proxies=self.proxy  )
							print response.url
							jsonData = json.loads(response.content)
							if len(jsonData["data"]["list"])==0:#到了没有数据的页码
								break
							else:
								insertData = jsonData["data"]["list"]
								if len(insertData) != 0:
									rawData.extend(insertData)
							pageno += 1
					else:
						for pageno in apiConfig["params"]["pageNo"]:
							paramsReal["pageNo"] = pageno
							response  = requests.get( apiConfig['url'], params="&".join(["%s=%s"%(k,v) for k,v in paramsReal.items()]), headers=self.headers,cookies=self.cookies, proxies=self.proxy  )
							print response.url
							jsonData = json.loads(response.content)
							if len(jsonData["data"]["list"])==0:#到了没有数据的页码
								break
							else:
								rawData = jsonData["data"]["list"]
								if len(insertData) != 0:
									rawData.extend(insertData)

					for row in rawData:
						if len(row) < 17:
							row['chainGrowth']      = None
							row['chainGrowthTrend'] = None
						row['cat_id'] = catid
						rawInsertData.append( [row[k] for k in columnList ] )

				self.crawlToMysql( columnList, rawInsertData, MysqlConnect, tableName, dbConfig )
			else:
				print "crawl_data_industry_hotshops_list:data empty!"
		except Exception,e:
			print "ERROR:>crawl_data_industry_hotshops_list:",e



	def get_shop_item_get_market_p4p_list( self, url, params, pageno, itemID, columnList, rawInsertData, GET_SHOP_ITEM_GET_MARKET_P4P_LIST_STOP_FLAG ):
		params["pageNo"] = pageno
		response         = requests.get(url,params="&".join(["%s=%s"%(k,v) for k,v in params.items()]),headers=self.headers,cookies=self.cookies, proxies=self.proxy)
		print response.url

		jsonData         = json.loads(response.content)
		if len(jsonData["data"]["list"])==0:#到了没有数据的页码
			GET_SHOP_ITEM_GET_MARKET_P4P_LIST_STOP_FLAG.value = 1
		else:
			rawData = jsonData["data"]["list"]
			if len(rawData) != 0:
				for row in rawData:
					row['itemid'] = itemID
					row['date']   = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime( float(unicode(row['date'])[:-3]) ))
					rawInsertData.append( [row[k] for k in columnList ] )

	def get_shop_item_get_market_p4p_list_one_item(self, url, itemid, paramsReal, columnList, rawInsertData ):
		serverProcess = multiprocessing.Manager()
		GET_SHOP_ITEM_GET_MARKET_P4P_LIST_STOP_FLAG = serverProcess.Value("i",0)
		GET_SHOP_ITEM_GET_MARKET_P4P_LIST_STOP_FLAG.value = 0
		rawData = list()
		print itemid
		paramsReal["id"] = itemid
		if len(paramsReal["pageNo"]) == 0:
			pageno    = 1
			pageStage = 5
			while GET_SHOP_ITEM_GET_MARKET_P4P_LIST_STOP_FLAG.value != 1:
				jobs = list()
				for i in range(pageno,pageno+pageStage):
					p = multiprocessing.Process(target=self.get_shop_item_get_market_p4p_list, args=(url,paramsReal, i, itemid,columnList, rawInsertData,GET_SHOP_ITEM_GET_MARKET_P4P_LIST_STOP_FLAG,))
					p.start()
					jobs.append(p)
				for p in jobs:
					p.join()
				pageno+=pageStage
		else:
			for pageno in paramsReal["pageNo"]:
				paramsReal["pageNo"] = pageno
				response  = requests.get( url, params="&".join(["%s=%s"%(k,v) for k,v in paramsReal.items()]),headers=self.headers, cookies=self.cookies, proxies=self.proxy  )
				print response.url
				jsonData = json.loads(response.content)
				if len(jsonData["data"]["list"])==0:#到了没有数据的页码
					break
				else:
					rawData = jsonData["data"]["list"]
					if len(rawData) != 0:
						rawData.extend(rawData)
		for row in rawData:
			row['itemid'] = itemid
			row['date'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime( float(unicode(row['date'])[:-3]) ))
			rawInsertData.append( [row[k] for k in columnList ] )

	def crawl_shop_item_get_market_p4p_list(self, userConfig, MysqlConnect, dbConfig, itemIDList):
		try:
			apiConfig = userConfig["APIConfig"]['shop_item_get_market_p4p_list']
			apiConfig["params"]["id"] = list(itemIDList) if itemIDList is not None else apiConfig['id']
			uid       = userConfig["uid"]
			deltaDays = apiConfig["deltaDays"]
			itemIDList = list(itemIDList)
			SeverProcess = multiprocessing.Manager()
			if len(apiConfig["params"]["id"]) == 0:
				MysqlConnect.sql           = "SELECT DISTINCT auction_id FROM dim_auction WHERE seller_id = %s"%uid
				MysqlConnect.reConnect()
				itemList                   = MysqlConnect.query(0)
				apiConfig["params"]["id"] = [item[0] for item in itemList]
			tableName  = apiConfig["tableName"]
			columnList = apiConfig["columnList"]
			paramsReal    = copy.deepcopy( apiConfig["params"] )

			paramsReal["startDate"] = int( time.mktime( (datetime.datetime.now() - datetime.timedelta(deltaDays)).timetuple() ) ) * 1000
			paramsReal["endDate"]   = int( time.mktime(time.localtime()) ) * 1000

			if len(apiConfig["params"]["id"] ) != 0:
				itemStage = 30
				itemIdListLen = len(apiConfig["params"]["id"])
				for i in xrange(0, itemIdListLen,itemStage):
					rawInsertData = SeverProcess.list()
					jobs         = list()
					itemListTemp = itemIDList[i:i+itemStage-1]
					for j in range(0,len(itemListTemp)):
						paramsReal["id"] = itemListTemp[j]
						p = multiprocessing.Process( target=self.get_shop_item_get_market_p4p_list_one_item, args=(apiConfig["url"], itemListTemp[j],paramsReal, columnList,rawInsertData,) )
						p.start()
						jobs.append(p)
					for p in jobs:
						p.join()
					rawInsertData = list(rawInsertData)
					self.crawlToMysql( columnList, rawInsertData, MysqlConnect, tableName, dbConfig )
			else:
				print "crawl_shop_item_get_market_p4p_list:data empty!"
		except Exception,e:
			print "ERROR:>crawl_shop_item_get_market_p4p_list:",e

	def get_data_item_market_tbk(self, url, params, pageno, columnList, rawInsertData, GET_DATA_ITEM_MARKET_TBK_STOP_FLAG):
		params["pageNo"] = pageno
		response         = requests.get(url,params="&".join(["%s=%s"%(k,v) for k,v in params.items()]),headers=self.headers,cookies=self.cookies, proxies=self.proxy)
		print response.url
		jsonData         = json.loads(response.content)
		if len(jsonData["data"]["list"])==0:#到了没有数据的页码
			GET_DATA_ITEM_MARKET_TBK_STOP_FLAG.value = 1
		else:
			rawData = jsonData["data"]["list"]
			if len(rawData) != 0:
				for row in rawData:
					row['date'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime( float(unicode(row['date'])[:-3]) ))
					rawInsertData.append( [row[k] for k in columnList ] )

	def get_data_item_market_tbk_one_item(self, url, itemid, paramsReal, columnList, rawInsertData ):
		serverProcess = multiprocessing.Manager()
		GET_DATA_ITEM_MARKET_TBK_STOP_FLAG = serverProcess.Value("i",0)
		GET_DATA_ITEM_MARKET_TBK_STOP_FLAG.value = 0
		rawData = list()
		print itemid
		paramsReal["id"] = itemid
		if len(paramsReal["pageNo"]) == 0:
			pageno    = 1
			pageStage = 5
			while GET_DATA_ITEM_MARKET_TBK_STOP_FLAG.value != 1:
				jobs = list()
				for i in range(pageno,pageno+pageStage):
					p = multiprocessing.Process(target=self.get_data_item_market_tbk, args=(url,paramsReal, i,columnList, rawInsertData,GET_DATA_ITEM_MARKET_TBK_STOP_FLAG,))
					p.start()
					jobs.append(p)
				for p in jobs:
					p.join()
				pageno+=pageStage
		else:
			for pageno in paramsReal["pageNo"]:
				paramsReal["pageNo"] = pageno
				response  = requests.get( url, params="&".join(["%s=%s"%(k,v) for k,v in paramsReal.items()]),headers=self.headers, cookies=self.cookies, proxies=self.proxy  )
				print response.url
				jsonData = json.loads(response.content)
				if len(jsonData["data"]["list"])==0:#到了没有数据的页码
					break
				else:
					rawData = jsonData["data"]["list"]
					if len(rawData) != 0:
						rawData.extend(rawData)
		for row in rawData:
			row['date'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime( float(unicode(row['date'])[:-3]) ))
			rawInsertData.append( [row[k] for k in columnList ] )

	def crawl_data_item_market_tbk(self, userConfig, MysqlConnect, dbConfig, itemIDList):
		try:
			SeverProcess = multiprocessing.Manager()
			apiConfig = userConfig["APIConfig"]['data_item_market_tbk']
			apiConfig["params"]["id"] = list(itemIDList) if itemIDList is not None else apiConfig['id']
			uid       = userConfig["uid"]
			deltaDays = apiConfig["deltaDays"]
			if len(apiConfig["params"]["id"]) == 0:
				MysqlConnect.sql = "SELECT DISTINCT auction_id FROM dim_auction WHERE seller_id = %s"%unicode(uid)
				MysqlConnect.reConnect()
				itemList         = MysqlConnect.query(0)
				apiConfig["params"]["id"] = [item[0] for item in itemList]

			tableName     = apiConfig["tableName"]
			columnList    = apiConfig["columnList"]
			rawInsertData = SeverProcess.list()
			paramsReal    = copy.deepcopy( apiConfig["params"] )

			paramsReal["startDate"] = int( time.mktime( (datetime.datetime.now() - datetime.timedelta(deltaDays)).timetuple() ) ) * 1000
			paramsReal["endDate"]   = int( time.mktime(time.localtime()) ) * 1000

			if len(apiConfig["params"]["id"] ) != 0:
				itemStage = 30
				itemIdListLen = len(apiConfig["params"]["id"])

				for i in xrange(0, itemIdListLen,itemStage):
					rawInsertData = SeverProcess.list()
					jobs         = list()
					itemListTemp = itemIDList[i:i+itemStage-1]
					for j in range(0,len(itemListTemp)):
						paramsReal["id"] = itemListTemp[j]
						p = multiprocessing.Process( target=self.get_data_item_market_tbk_one_item, args=(apiConfig["url"], itemListTemp[j],paramsReal, columnList,rawInsertData,) )
						p.start()
						jobs.append(p)
					for p in jobs:
						p.join()
					rawInsertData = list(rawInsertData)
					self.crawlToMysql( columnList, rawInsertData, MysqlConnect, tableName, dbConfig )

				self.crawlToMysql( columnList, rawInsertData, MysqlConnect, tableName, dbConfig )
			else:
				print "crawl_data_item_market_tbk:data empty!"
		except Exception,e:
			print "ERROR:>crawl_data_item_market_tbk:",e

	def get_shop_get_offer_list_insertData(self, url, params, itemID, rawInsertData, columnList, itemInfo):
		response = requests.get( url,  params="&".join(["%s=%s"%(k,v) for k,v in params.items()]), headers=self.headers,cookies=self.cookies, proxies=self.proxy  )
		print response.url
		rawData              = json.loads(response.content)['data']
		for row in rawData:
			row['itemid'] = itemID
			row['date']   = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime( float(unicode(row['date'])[:-3]) ))
			row['shopid'] = itemInfo['shopId']
			row['title']  = itemInfo['title']
			row['sellerNick'] = itemInfo['sellerNick']
			row['brand']  = itemInfo['brand']
			row['cid']    = itemInfo['catId']

			if row["offer"] != 0:
				row['avg_price'] = float(row["price"]) / float(row["offer"])
			else:
				row['avg_price'] = 0
			rawInsertData.append( [row[k] for k in columnList ] )

	def crawl_shop_get_offer_list(self, userConfig, MysqlConnect, dbConfig, itemList, itemIDList):
		try:
			serverProcess = multiprocessing.Manager()

			apiConfig = userConfig["APIConfig"]['mj_hotitems_info']
			deltaDays = apiConfig["deltaDays"]
			print apiConfig
			apiConfig["params"]["itemId"] = list(itemIDList) if itemIDList is not None else apiConfig["params"]["itemId"]
			print 'here'
			tableName     = apiConfig["tableName"]
			columnList    = apiConfig["columnList"]
			rawInsertData = serverProcess.list()
			paramsReal    = copy.deepcopy( apiConfig["params"] )

			paramsReal["startDate"] = int( time.mktime( (datetime.datetime.now() - datetime.timedelta(deltaDays)).timetuple() ) ) * 1000
			paramsReal["endDate"]   = int( time.mktime(time.localtime()) ) * 1000

			if len(apiConfig["params"]["itemId"] ) != 0:
				itemStage = 40
				for i in xrange(0,len(itemIDList),itemStage):
					jobs             = list()
					itemListTemp     = itemIDList[i:i+itemStage-1]
					itemInfoListTemp = itemList[i:i+itemStage-1]
					for j in range(0,len(itemListTemp)):
						paramsReal["itemId"] = itemListTemp[j]
						p = multiprocessing.Process( target=self.get_shop_get_offer_list_insertData, args=(apiConfig["url"],paramsReal, itemListTemp[j], rawInsertData, columnList,itemInfoListTemp[j]) )
						p.start()
						jobs.append(p)
					for p in jobs:
						p.join()

				rawInsertData = list(rawInsertData)
				self.crawlToMysql( columnList, rawInsertData, MysqlConnect, tableName, dbConfig )
			else:
				print "crawl_shop_get_offer_list:data empty!"
		except Exception,e:
			print "ERROR:>crawl_shop_get_offer_list:",e


	def crawlToMysql(self, columnList, insertData, MysqlConnect, tableName, dbConfig):
		MysqlConnect.sql  = "REPLACE INTO %s "%tableName
		MysqlConnect.sql += "( %s ) " %(",".join(columnList))
		MysqlConnect.sql += "VALUES( %s )" %(",".join(["%s" for i in xrange(0, len(columnList))]))
		MysqlConnect.reConnect()
		updateState       = MysqlConnect.updateMany( insertData )
		if not updateState:
			MysqlConnect.sql  = dbConfig[tableName] #获取创建对应数据库的SQL
			MysqlConnect.update()
			MysqlConnect.sql  = "REPLACE INTO %s "%tableName
			MysqlConnect.sql += "( %s ) " %(",".join(columnList))
			MysqlConnect.sql += "VALUES( %s )" %(",".join(["%s" for i in xrange(0, len(columnList))]))
			MysqlConnect.updateMany( insertData )

	def crawlDataToMysql(self, loginScriptPath, username, userConfigData, MysqlConnect, crawlAPIList, dbConfig ):
		try:
			if len(crawlAPIList) != 0:
				self.login(loginScriptPath,username=username,passwd=userConfigData['passwd'])
				print self.cookies
				itemIdList = None
				itemList   = None
				whetheCrawlItemList = ("shop_item_get_market_p4p_list" in crawlAPIList) or ( "data_item_market_tbk" in crawlAPIList ) or ( "mj_hotitems_info" in crawlAPIList)
				if whetheCrawlItemList:
					itemList, itemIdList = self.get_data_industry_hotitems_list(userConfigData,MysqlConnect)
					itemIdList = list( itemIdList )
					itemList   = list( itemList )

				for crawlAPI in crawlAPIList:
					if crawlAPI == "data_industry_general_trend":
						self.crawl_data_industry_general_trend( userConfigData, MysqlConnect, dbConfig )
						print "done crawl_data_industry_general_trend!"
					elif crawlAPI == "data_industry_hotshops_list":
						self.crawl_data_industry_hotshops_list( userConfigData, MysqlConnect, dbConfig )
						print "done crawl_data_industry_hotshops_list!"
					elif crawlAPI == "data_item_market_tbk":
						self.crawl_data_item_market_tbk( userConfigData, MysqlConnect, dbConfig, itemIdList  )
						print "done crawl_data_item_market_tbk!"
					elif crawlAPI == "shop_item_get_market_p4p_list":
						self.crawl_shop_item_get_market_p4p_list( userConfigData, MysqlConnect, dbConfig, itemIdList  )
						print "done crawl_shop_item_get_market_p4p_list!"
					elif crawlAPI == "mj_hotitems_info":
						self.crawl_shop_get_offer_list( userConfigData, MysqlConnect, dbConfig, itemList, itemIdList )
						print "done mj_hotitems_info"
		except Exception,e:
			print "***************"
			print e
			print "****************"

if __name__ == "__main__":
	pass

