#-*- coding: utf-8 -*-
__author__ = 'XuWeitao'

import json
import MySQLdb

class RawMysql(object):
	def __init__(self, host="", port=0, user="", passwd="", db="", dbConfig="" ):
		try:
			self.sql = u""
			if host != "":
				self.host = host
				self.port = port
				self.user = user
				self.passwd = passwd
				self.db     = db
				self.connect = MySQLdb.connect( host=host, port=port, user=user, passwd=passwd, db=db, charset='utf8' )
			else:

				config = json.loads( open( r"E:\xuweitao\WebSpider\taobao\DBconfigure.json" if dbConfig == "" else dbConfig ).read() )
				self.host    = config['host']
				self.port    = config['port']
				self.user    = config['user']
				self.passwd  = config['passwd']
				self.db      = db if db != "" else config['database']
				self.connect = MySQLdb.connect( host=config['host'], port=config['port'], user=config['user'],
				                                passwd=config['passwd'], db=db if db != "" else config['database'], charset='utf8' )
			self.cursor = self.connect.cursor()
		except MySQLdb.Error, e:
			pass


	def query(self, size=1):
		"""
		执行sql，返回记录数由size指定，默认为1，设置成0则全部返回
		:param size:返回的记录数，默认为1，为0时全部返回
		:return:返回查询结果记录集
		"""
		self.cursor.execute(self.sql)
		return self.cursor.fetchmany(size=size) if size != 0 else self.cursor.fetchall()

	def update(self, arguTuple=()):
		"""
		执行数据库更新操作，如插入删除等
		"""
		try:
			self.cursor.execute( self.sql, arguTuple )
			self.connect.commit()
			return True
		except Exception,e:
			print e
			self.connect.rollback()
			return False

	def updateMany(self, arguList=None):
		"""
		执行数据库批量DML操作，如批量插入
		:param arguList:需要传入一个列表，列表中的元素为包含传入参数的元组，sql为带占位符的sql
		"""
		if arguList is None:
			arguList = []
		try:

			self.cursor.executemany( self.sql, arguList )
			self.connect.commit()
			return True
		except Exception,e:
			print e
			self.connect.rollback()
			return False

	def reConnect(self):
		self.connect = MySQLdb.connect( host=self.host, port=self.port, user=self.user,
				                                passwd=self.passwd, db=self.db, charset='utf8' )
		self.cursor = self.connect.cursor()

if __name__ == "__main__":
	pass
	# import cPickle
	# import chardet
	# Raw = RawMysql( "localhost", 3306, 'root', 'Sgy323', 'db_1023957254' )
	# Raw.sql = "SELECT * FROM dim_auction"
	# target = Raw.query(1)
	# Raw.reConnect()
	# Raw.query(1)
	# print target
	# print target[0][0]
	# print chardet.detect(target[0][0])
	# import base64
	# print base64.b64decode( target[0][0] )
	# print cPickle.load(open(target[0][0],"rb"))


