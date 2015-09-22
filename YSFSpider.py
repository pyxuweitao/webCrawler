# -*- encoding: utf-8 -*-
__author__ = 'XuWeitao'
import time
from YSF.YSFCrawler import *
from PythonRawMysql.Mysql import *
import json

def funcCrawlTablesToLocalDB( tableList, YSF, MysqlConnect, length = 5000):
	"""
	根据传入的表名列表参数来讲该表数据本地化
	:param tableList:表名称列表
	:param YSF:御膳房爬虫对象
	:param MysqlConnect:数据库连接对象
	:param length:每次取多少条 <=5000
	:return:
	"""

	for tableName in tableList:
		start = 0
		while True:
			state = YSF.crawlDataToMySQL(MysqlConnect,tableName, start, length)
			print state
			if state:
				start += length
			else:
				break
		print "done ", tableName

if __name__ == "__main__":
	YSFConfigPath = r"YSF\YsfConfig.json"
	DBConfigPath  = r"YSF\DBConfig.json"
	with open(YSFConfigPath) as YSFConfigFile:
		YSFConfig = json.loads( YSFConfigFile.read() )

	Raw = RawMysql(db="YSF",dbConfig=DBConfigPath)
	ysf = YsfCrawler(YSFConfigPath)
	#ysf.crawlDataToMySQL( Raw,  u"ump_raw_shop_platform_region_view_d", start=0, length=5000)
	tableNameList = [ table for table in YSFConfig['tableIDMapping'] ]
	funcCrawlTablesToLocalDB( tableNameList, ysf, Raw )
