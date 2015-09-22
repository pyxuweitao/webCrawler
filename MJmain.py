# -*- encoding: utf-8 -*-
__author__ = 'XuWeitao'

from PythonRawMysql.Mysql import *
from MJ.MJCrawler import *
import json
import requests

if __name__ == "__main__":
	loginScriptPath = r"MJ\loginForPhantom.js"
	with open(r"MJ\MjUserConfig.json") as ConfigFile:
		mjConfig = json.loads(ConfigFile.read())


	with open(r"MJ\MJCrawler.json") as CrawlerConfigFile:
		crawlerConfig = json.loads( CrawlerConfigFile.read() )

	with open(r"MJ\DBconfig.json") as MjDBConfig:
		mjDBConfig = json.loads( MjDBConfig.read() )

	try:
		ipjson = {"http":"http://"+crawlerConfig["proxy"]["ip"] +":"+ unicode(crawlerConfig["proxy"]["port"])}
		response = requests.get("http://www.baidu.com",proxies=ipjson)
		if u"百度一下" not in response.content.decode("utf-8"):
			raise Exception
	except Exception,e:
		print e
		print "代理出现异常，请更换代理配置（最好是端口为80的）"
	else:
		mj = MjCrawler(proxy=ipjson)

		for username in crawlerConfig["users_to_crawl"]:
			Raw = RawMysql(dbConfig="MJ\DBConfig.json", db=mjConfig[username]["database"])
			mj.crawlDataToMysql( loginScriptPath, username, mjConfig[username], Raw, crawlerConfig['crawler_config'][username], mjDBConfig["createTableSQL"] )

		print "done!"
