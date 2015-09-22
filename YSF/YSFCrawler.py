# -*- coding: utf-8 -*-
__author__ = 'XuWeitao'

import json
import requests

class YsfCrawler(object):
	def __init__(self, configPath=None):
		try:
			if configPath is  None:
				configPath = "YsfConfig.json"
			with open( configPath ) as config:
				configDict = json.loads(config.read())
				self.APIurl = configDict['APIurl']
				self.tableIDMapping = configDict['tableIDMapping']
		except Exception,e:
			print u"YsfCrawler.__init__:"+unicode(e)

	def crawlAPI(self, tableName, start=0, length=5000):
		"""
		爬取接口对应的json数据，返回一个字典
		:param tableName:数据表名
		:param start:获取数据记录的条数从第start条开始
		:param length:获取数据记录的条数
		:return:获取python可以解析的字典
		"""
		try:
			paraDict = {"id":self.tableIDMapping[tableName]['id'], "start":start, "length":length}
			print 'here'
			print r"&".join( "%s=%s" %(k,v) for k,v in paraDict.items() )
			response = requests.get( self.APIurl, params = r"&".join( "%s=%s" %(k,v) for k,v in paraDict.items() ) )
			print 'get!'
			print "==========="
			print response.content
			print '==========='
			return json.loads(response.content)
		except Exception,e:
			print u"YsfCrawler.crawlAPI:"+unicode(e)

	def resolveJsonToMysql(self, tableName, JSON, MySQLConnect):
		column_list = JSON["column_list"]['string']
		res_list    = JSON["row_list"]
		print '****************'
		print res_list.has_key("query_row")
		print '****************'
		if res_list.has_key( "query_row" ):
			res_list = res_list["query_row"]
		else:
			return False #取完所有数据
		insertData  = [ dic['values']['string'] for dic in res_list ]
		try:
			index = column_list.index( "dt" )
			column_list.pop(index)
			for row in insertData:
				row.pop( index )
		except ValueError:
			index     = -1
		columnLen = len(column_list)
		try:
			MySQLConnect.sql  = "REPLACE INTO %s "%tableName
			#MySQLConnect.sql += "( %s ) "%",".join(column_list)
			MySQLConnect.sql += "VALUES( %s )"%",".join([r"%s" for i in xrange(0,columnLen)])
			state = MySQLConnect.updateMany( insertData )
			if state:
				print "done write into %s"%tableName
			else:
				raise Exception
		except Exception,e:
			print e
			MySQLConnect.sql = self.tableIDMapping[tableName]['CreateSQL']
			MySQLConnect.update()
			try:
				MySQLConnect.sql  = "REPLACE INTO %s "%tableName
				#MySQLConnect.sql += "( %s ) "%",".join(column_list)
				MySQLConnect.sql += "VALUES( %s )"%",".join([r"%s" for i in xrange(0,columnLen)])
				state = MySQLConnect.updateMany( insertData )
				if state:
					print "done write into %s"%tableName
				else:
					raise Exception
			except Exception,e:
				print '==========================='
				print e
				print insertData
				print MySQLConnect.sql
				print "ERROR>cannot write into %s"%tableName
				print '=============================='
		return True

	def crawlDataToMySQL(self, MySQLConnect, tableName, start=0, length=5000):
		"""
		爬取YSFAPI数据到数据库
		:param MySQLConnect:数据库连接对象
		:param tableName:数据表名
		:param start:记录起始位置
		:param length:select出的记录条数
		:return:如果有异常或者API接口已经获取不到数据，就返回False，否则返回True
		"""
		try:
			return self.resolveJsonToMysql(tableName,self.crawlAPI( tableName=tableName, start=start, length=length ),MySQLConnect)
		except Exception,e:
			print u"YsfCrawler.crawlDataToMySQL:"+unicode(e)
			return False

if __name__=="__main__":
	pass