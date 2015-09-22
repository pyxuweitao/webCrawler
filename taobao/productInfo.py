#-*- encoding: utf-8 -*-
import sys,os
sys.path.append(r"e:\\xuweitao\\webspider\\taobao\\")
from PythonRawMysql import Mysql
import multiprocessing
import subprocess
import yaml
import json
import MySQLdb

UPDATE_DATA = []

__author__ = 'XuWeitao'


def getItemAttr(itemID):
	print itemID
	reload(sys)
	sys.setdefaultencoding("utf-8")
	cmd     = 'phantomjs %s %s' %(r"\sources\detailItem.js", itemID )
	proc    = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
	info = ""
	for row in proc.stdout.readlines():
		if row.startswith("{"):
			if "{}" not in row:
				row = row.decode("utf-8")[1:]
				row = row.replace("&nbsp;","").replace("：",":").split("@")[:-1]
				for i, kv in enumerate(row):
					row[i] = u'"'+unicode(kv.split(":")[0])+u'"'+u':'+u'"'+unicode(kv.split(":")[1])+u'"'
				info = row
				resJSON = "{"+u",".join(info)+"}"
				print resJSON
				return resJSON
			else:
				return None


def writeIntoMysql(MysqlConnect, paramList ):
	try:
		MysqlConnect.sql = "UPDATE raw_crawl_shop_item SET itemAttrs = %s WHERE itemid = %s"
		MysqlConnect.updateMany( paramList )
	except Exception,e:
		print e

def getAllShopItemID(MysqlConnect):

	try:
		MysqlConnect.sql = "SELECT DISTINCT itemid FROM raw_crawl_shop_item "
		print MysqlConnect.sql
		result = MysqlConnect.query(0)
	except Exception,e:
		print e
		result = []
	return result



def process(itemID):
	resJson = getItemAttr( itemID )
	UPDATE_DATA.append( ( resJson, itemID ))

if __name__=="__main__":
	with open(r"conf/productInfoConfig.json") as fi:
		data          = json.loads( fi.read() )
		database_list = data['databaseList']
		processStage  = data['processStage']
	print u"要执行的数据库为："
	print database_list
	conf_file_path = "conf/crawl.conf"
	conf_file      = open( conf_file_path )
	conf           = yaml.load( conf_file )
	host           = conf['host']
	port           = conf['port']
	user           = conf['user']
	password       = conf['password']

	for db in database_list:
		db         = db
		Raw        = Mysql.RawMysql(host=host, port=port,user=user,passwd=password, db=db )
		itemList = [ item[0] for item in getAllShopItemID(Raw) ]
		paramList  = []
		for i in range( 0, len(itemList), processStage ):
			itemListTemp = itemList[i:i+processStage]
			job = []
			for itemID in itemListTemp:
				p   = multiprocessing.Process( target = process, args = (itemID,) )
				p.start()
				job.append( p )
			for p in job:
				p.join( )

	print u"执行完毕！"