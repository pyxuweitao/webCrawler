# -*- encoding: utf-8 -*-
from __future__ import print_function

__author__ = 'XuWeitao'

import sys, os, MySQLdb
import urllib2, urllib, time, re, socket, cookielib, random
import json
import requests
#from BeautifulSoup import BeautifulSoup
from bs4 import BeautifulSoup
import multiprocessing
#import mysql.connector
import yaml


PROXYJSON = dict()

def getDate( ):
	date = time.strftime( "%Y-%m-%d", time.localtime( ) )
	return date


def formatDateStr( datestr ):
	tempdate = time.strptime( datestr, '%Y%m%d%H%M%S' )
	day = time.strftime( '%Y-%m-%d', tempdate )
	hour = time.strftime( '%H%M', tempdate )
	return [day, hour]


def getTask( host, port, user, password, database, tablename, itemstage = 1 ):
	db = MySQLdb.connect( host = host, port = port, user = user, passwd = password, db = database, charset = "utf8" )
	dbconn = db.cursor( )
	try:
		queryTask = "SELECT `dbname`,r_table,w_table,keyword,rule FROM %s.%s WHERE taskid = '%s'"
		print( queryTask % (database, tablename, itemstage) )
		dbconn.execute( queryTask % (database, tablename, itemstage) )
		result = dbconn.fetchall( )
		db.commit( )
	except:
		result = []
	dbconn.close( )
	return result

def getProxy(host,port,user,password, database, tablename):
	db = MySQLdb.connect( host=host, port=port, user=user, passwd=password, db=database, charset="utf8" )
	dbconn = db.cursor()
	try:
		queryTask = "SELECT DISTINCT ip, port FROM %s.%s LIMIT 1,10"
		print( queryTask % (database, tablename ) )
		dbconn.execute( queryTask % (database, tablename) )
		result = dbconn.fetchall( )
		db.commit( )
	except:
		result = []
	dbconn.close( )
	return result

def getSubTask( host, port, user, password, database, shop_tbname, query_rule ):
	# keyword,pagenumber = 1,ratesum = "",location = "",cat = "",brand = "",ppath = "",sort = "sale-desc")
	db = MySQLdb.connect( host = host, port = port, user = user, passwd = password, db = database, charset = "utf8" )
	dbconn = db.cursor( )
	try:
		queryTask = "SELECT DISTINCT uid FROM %s.%s %s" % (database, shop_tbname, query_rule)
		dbconn.execute( queryTask )
		result = dbconn.fetchall( )
		db.commit( )

	except Exception, e:
		print( e )
		result = []
	dbconn.close( )
	return result


def GenerateURL( uid, keyword, search_rule, inshops = 0 ):
	keyword = urllib.quote( keyword.encode( "utf-8" ) )
	url = 'http://s.taobao.com/search?inshopn=128&inshops=0&userids=' + str(
		uid ) + '&q=' + keyword + search_rule + '&app=api&m=get_shop_auctions'
	print( url )
	return url


def makeCookie( ):
	# 生成 Cookie 支持
	cookie = cookielib.LWPCookieJar( )
	cookie_support = urllib2.HTTPCookieProcessor( cookie )
	return cookie_support


def openPage( url ):
	# 使用代理 IP 打开页面
	##    keyword = urllib.quote(keyword.encode("utf8"))
	#ipJson =  {'http':'http://'+str(ip[0][0])+':'+str(ip[0][1])}

	global PROXYJSON

	#ipJson = { }
	#time.sleep(5)
	proxy_handler = urllib2.ProxyHandler( PROXYJSON )
	opener = urllib2.build_opener( makeCookie( ), urllib2.HTTPHandler, proxy_handler )
	urllib2.install_opener( opener )
	# 生成 URL
	url_referer = 'http://s.taobao.com/search?q=&commend=all&ssid=s5-e&search_type=shop&app=shopsearch'
	# 加载 URL 头
	headers = { "GET": url, "Accept": "*/*", "Connection": "keep-alive", "Host": "s.taobao.com", "Referer": url_referer,
	            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.69 Safari/537.36" }

	req = urllib2.Request( url )
	for header in headers:
		req.add_header( header, headers[header] )
	page = opener.open( req, None, 20 )
	return page


def soupPage( page, encode = "utf8" ):
	soup = BeautifulSoup( page, "html.parser", from_encoding = encode )
	return soup


def reSoup( soup ):
	pageData = re.sub( "&gt;", ">", str( soup ) )
	pageData = re.sub( "&lt;", "<", str( soup ) )
	pageData = re.sub( "</span>", "", str( soup ) )
	pageData = re.sub( "<span class=\"H\">", "", str( pageData ) )
	return pageData


def reMove( data ):
	temp = re.sub( "</span>", "", data )
	temp = re.sub( "<span class=\"H\">", "", temp )
	temp = re.sub( "\'", "", temp )
	temp = re.sub( "\\\\", "", temp )
	return temp


def getData( uid, keyword, search_rule = '', inshops = 1 ):
	url = GenerateURL( uid, keyword, search_rule, inshops )
	page = openPage( url )
	updatetime = getDate( )
	soup = soupPage( page )
	pageData = reSoup( soup )
	data = []
	print( "ok" )
	##    pagejson = json.loads(str(pageData))
	try:
		pagejson = json.loads( str( pageData ) )
	except Exception, e:
		pagejson = json.loads( '{"API.SSInshopApi":{"auctions":[]}}' )
		print( uid, "banned banned bad:", e )
		#print(str(pageData))
	try:
		shoppage = pagejson["API.SSInshopApi"]["auctions"]
	except:
		# 页面出现异常无法解析到所需JSON格式，即可能页面内容已经被删除
		print( "error:bad error" )
		shoppage = []

	for i in range( 0, len( shoppage ) ):
		try:
			uid = shoppage[i]["user_id"]
			quantity = shoppage[i]["quantity"]
			total_sold_quantity = shoppage[i]["total_sold_quantity"]
			people_num = shoppage[i]["people_num"]
			ordercost = shoppage[i]["ordercost"]
			dsr_desc = shoppage[i]["grade_avg"]
			cid = shoppage[i]["category"]
			old_starts = shoppage[i]["old_starts"]
			try:
				old_startdate = formatDateStr( old_starts )[0]
			except:
				old_startdate = '1970-01-01'
				print( 'startdate format error' )
			sellernick = shoppage[i]["nick"]
			ratesum = shoppage[i]["ratesum"]
			shipping_fee = shoppage[i]["real_post_fee"]
			comment_count = shoppage[i]["comment_count"]
			if (comment_count == ''):
				comment_count = '0'

			user_type = shoppage[i]["user_type"]

			itemid = shoppage[i]["nid"]

			print(itemid)

			###爬取商品属性
			#itemAttrsTemp = getItemAttr(unicode(itemid))

			#if itemAttrsTemp is not None:
			#	itemAttrs = json.dumps(itemAttrsTemp,ensure_ascii=False)
			#else:
			#	itemAttrs = None #None表示下架
			#print(itemAttrs)
			####爬取商品属性


			biz30day = shoppage[i]["biz30day"]
			volume30day = shoppage[i]["volume30day"]

			cc_score1 = shoppage[i]["cc_score1"]
			## Using MariaDB 10+ Dynamic Column Storage
			pidvid = re.sub( "\s", ",", shoppage[i]["pidvid"] )
			if pidvid == '':
				pidvid = '0:0'
			try:
				bid = re.findall( '20000:([-]?\d+)', pidvid )[0]
			except:
				bid = -1

			scid = shoppage[i]["scid"]

			startdate = shoppage[i]["starts"]
			enddate = shoppage[i]["ends"]
			try:
				new_startdate = formatDateStr( startdate )
				startdate_date = new_startdate[0]
				startdate_hour = new_startdate[1]
			except:
				startdate_date = '1970-01-01'
				startdate_hour = '0000'
				print( 'startdate format error' )

			#support_bonus = shoppage[i]["support_bonus"]
			vip = shoppage[i]["vip"]

			zk_final_price = shoppage[i]["zk_final_price"]

			price = round( float( zk_final_price ), 0 )

			zk_final_price_wap = shoppage[i]["zk_final_price_wap"]

			if (zk_final_price_wap == ''):
				zk_final_price_wap = 0
			sp_service = shoppage[i]["sp_service"]
			ext_discount_price = shoppage[i]["ext_discount_price"]
			ext_pict_url = shoppage[i]["ext_pict_url"]

			try:
				title = reMove( shoppage[i]["ext_raw_title"] )
			except Exception, e:
				print( 'Title phrase error:', e, 'title data:', shoppage[i]["ext_raw_title"] )
				title = ""
			total_fee = float( zk_final_price ) * float( volume30day )
			# datatemp = (
			# updatetime, old_startdate, total_fee, price, bid, title, uid, quantity, total_sold_quantity, people_num,
			# ordercost, dsr_desc, cid, sellernick, ratesum, shipping_fee, comment_count, user_type, itemid, biz30day,
			# volume30day, cc_score1, pidvid, startdate_date, startdate_hour, vip, zk_final_price, zk_final_price_wap,
			# ext_pict_url, itemAttrs)
			datatemp = (
			updatetime, old_startdate, total_fee, price, bid, title, uid, quantity, total_sold_quantity, people_num,
			ordercost, dsr_desc, cid, sellernick, ratesum, shipping_fee, comment_count, user_type, itemid, biz30day,
			volume30day, cc_score1, pidvid, startdate_date, startdate_hour, vip, zk_final_price, zk_final_price_wap,
			ext_pict_url)
		except Exception, e:
			print( "#INNER JSON_PHRASE_ERROR#", e )
		data.append( datatemp )
	return data


def rephrase( data ):
	if data == -1:
		data = '0:0'
		data_colum = data.split( ',' )
	else:
		data_colum = data.split( ',' )
	initial_str = ''
	for i in range( 0, len( data_colum ) ):
		data_column_phrased = "'" + re.sub( ":", "','", data_colum[i] ) + "'"
		if i == 0:
			initial_str = initial_str + 'COLUMN_CREATE(' + data_column_phrased + ')'
		else:
			initial_str = 'COLUMN_ADD(' + initial_str + ',' + data_column_phrased + ')'
	return initial_str


def newmany( data ):
	try:
		NewSQLString = ''
		newmany = '''('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','''
		newmany2 = ''','%s','%s','%s','%s','%s','%s')'''
		#newmany2 = ''','%s','%s','%s','%s','%s','%s','%s')'''

		for i in range( 0, len( data ) ):
			# Function for DYNAMIC COLUMN
			rephrased_str = rephrase( data[i][22] )
			#
			NewSQLString = NewSQLString + newmany % data[i][:22] + rephrased_str + newmany2 % data[i][23:] + ','
		return NewSQLString[:-1]
	except TypeError,e:
		print(data)

def crawl_item_data( info ):
	host = info[0]
	port = info[1]
	user = info[2]
	password = info[3]
	database = info[4]
	tbname = info[5]
	keyword = info[6]
	search_rule = info[7]
	uid = info[8]

	try:
		itemdata = getData( uid, keyword, search_rule, 4 )
	except Exception, e:
		itemdata = [(getDate( ), '1970-01-01', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '0:0',
		             '1970-01-01', 'HOUR', 0, 0, 0, 0)]
		# itemdata = [(getDate( ), '1970-01-01', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '0:0',
		#              '1970-01-01', 'HOUR', 0, 0, 0, 0, None)]
		print( "Error:", e )
	if itemdata == []:
		# itemdata = [(getDate( ), '1970-01-01', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '0:0',
		#              '1970-01-01', 'HOUR', 0, 0, 0, 0, None)]
		itemdata = [(getDate( ), '1970-01-01', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '0:0',
		             '1970-01-01', 'HOUR', 0, 0, 0, 0)]

	db = MySQLdb.connect( host = host, port = port, user = user, passwd = password, db = database, charset = "utf8" )
	dbconn = db.cursor( )

	NewSQLString = newmany( itemdata )
	NewSQLString = NewSQLString.encode( 'utf-8' )

	ItemDataInsert = "REPLACE INTO " + str(
		tbname ) + " (updatetime,old_starts,total_fee,price,bid,title,uid,quantity,total_sold_quantity,people_num,ordercost,dsr_desc,cid,sellernick," \
	               "ratesum,shipping_fee,comment_count,user_type,itemid,biz30day,volume30day,cc_score1,pidvid,startdate_date,startdate_hour,vip," \
	               "zk_final_price,zk_final_price_wap,ext_pict_url) VALUES" + NewSQLString
	try:
		#print(ItemDataInsert)
		dbconn.execute( ItemDataInsert )
	except Exception, e:
		print( e )
		#f = open('D://xxxx.txt','w')
		#f.write(ItemDataInsert)
		#f.close()
		print( 'logged' )
	db.commit( )
	db.close( )


def multiTask( tasklist, host, port, user, password, database, item_tbname, keyword, search_rule ):
	stage = 100
	for i in range( 0, len( tasklist ), stage ):
		tasktemp = tasklist[i:i + stage]
		job = []
		if i < stage:
			print( getDate( ) + ":" + "Begin_Project:" + str( len( tasklist ) ) )
		print( getDate( ) + ":" + "Process:" + str( round( (i + 10) * 100 / len( tasklist ), 0 ) ) + "%" )
		for j in range( 0, len( tasktemp ) ):
			ptask = (host, port, user, password, database, item_tbname, keyword, search_rule, tasktemp[j][0])
			# info
			p = multiprocessing.Process( target = crawl_item_data, args = (ptask,) )
			p.start( )
			job.append( p )
		for p in job:
			p.join( )


def do_crawl_item( host, port, user, password, database, shop_tbname, write_table, keyword, rule, initial_str ):
	rule_json = json.loads( rule.encode( 'utf-8' ) )
	query_rule = rule_json["query_rule"]
	search_rule = rule_json["search_rule"]
	taskList = getSubTask( host, port, user, password, database, shop_tbname, query_rule )
	initialTable( host, port, user, password, database, write_table, initial_str )
	multiTask(taskList,host,port,user,password,database,write_table,keyword,search_rule)
	# for j in range( 0, len( taskList ) ):
	# 	ptask = (host, port, user, password, database, write_table, keyword, search_rule, taskList[j][0])
	# 	crawl_item_data( ptask )


def initialTable( host, port, user, password, database, tbname, initial_str ):
	db = MySQLdb.connect( host = host, port = port, user = user, passwd = password, db = database, charset = "utf8" )
	dbconn = db.cursor( )
	try:
		dbconn.execute( initial_str % str( tbname ) )
		result = dbconn.fetchall( )
		db.commit( )
	except Exception, e:
		print( 'initial_table_failed', e )

	dbconn.close( )
	return


def writeStatus( host, port, user, password, database, shopid, pageinfo ):
	'''
	Log and current job status sent
	'''
	# keyword,pagenumber = 1,ratesum = "",location = "",cat = "",brand = "",ppath = "",sort = "sale-desc")
	db = MySQLdb.connect( host = host, port = port, user = user, passwd = password, db = database, charset = "utf8" )
	dbconn = db.cursor( )
	try:
		writeStatus = "REPLACE INTO pool_error_crawl_shop_item (updatetime,shopid,msg) VALUES (%s,%s,%s) "
		dbconn.execute( writeStatus )
		db.commit( )
	except:
		result = []

	dbconn.close( )
	return


def main( ):
	#-------- configuration part --------#
	# Connection Database
	conf_file_path = sys.path[0] + "/conf/crawl.conf"
	conf_file = open( conf_file_path )
	conf = yaml.load( conf_file )

	host = conf['host']
	port = conf['port']
	user = conf['user']
	password = conf['password']
	database = conf['conf_database']
	tablename = conf['conf_table']

	# Read initial_sql_table
	sql_file_path = sys.path[0] + "/conf/sql.ini"
	sql_file = open( sql_file_path )
	sql = yaml.load( sql_file )
	#print('SQL Print',sql)
	# SQL Section
	initial_str = sql['raw_crawl_shop_item']

	#---------------END-------------------#

	##    try:
	##        itemstage = sys.argv[1]
	##    except:
	##        itemstage = 22
	with open(r"conf/shopItemConfig.json") as fi:
		configData = json.loads( fi.read() )
	itemstage_list = configData["itemStageList"]
	try:
		ipjson = {"http":"http://"+configData["proxy"]["ip"] +":"+ unicode(configData["proxy"]["port"])}
		response = requests.get("http://www.baidu.com",proxies=ipjson)
		if u"百度一下" not in response.content.decode("utf-8"):
			raise Exception
	except Exception,e:
		print(e)
		print(u"代理出现异常，请更换代理配置（最好是端口为80的）")
	else:
		global PROXYJSON
		PROXYJSON = ipjson
		print( itemstage_list )
		for itemstage in itemstage_list:
			projectlist = getTask( host, port, user, password, database, tablename, itemstage )
			for project in projectlist:
				print( project )
				do_crawl_item( host, port, user, password, project[0], project[1], project[2], project[3], project[4],
			               initial_str )


if __name__ == "__main__":
	init = 1
	main( )
	#print(getItemAttr(unicode(272453)))


##    while True:
##        if init == 1:
##            print(time.localtime()[3],':',end='')
##            a = time.localtime()[3]
##            init = 0
##        if time.localtime()[3] > a:
##            print('\n',time.localtime()[3],':',end='')
##            a = time.localtime()[3]
##        if time.localtime()[3]- a<-10:
##            print('\n',time.localtime()[3],':',end='')
##            a = time.localtime()[3]
##        print(">",end='')

##        time.sleep(60)
##        if time.localtime()[3] == 1 and time.localtime()[4] <=2:
##            print("task_today_start:",time.localtime())
##            b = time.localtime()
##            '''

##            run the main job.
##            '''
##            main()
##            print("task_today_end!",time.localtime(),"from:",b)

