#-*- coding: utf8 -*-
__author__ = 'XuWeitao'
from PythonRawMysql import Mysql
from taobaoIndex import taobaoIndex
import json
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

def funcTaobaoIndexCrawl( UserName, ConfigPath, UserConfigPath, DBConfigPath, dbname=None ):
	taobaoIndexCrawler = taobaoIndex.TaobaoIndexCrawler( username=UserName,
	                               configPath=ConfigPath,
	                               userConfigPath=UserConfigPath)
	Raw     = Mysql.RawMysql(db=dbname,dbConfig=DBConfigPath) if dbname is not None else Mysql.RawMysql(db=taobaoIndexCrawler.dbname,dbConfig=DBConfigPath)
	#注意此处的profiles是Administor的profile，如果执行脚本的权限不够会出发shutil.Error，找不到文件的错误
	#if BSC.webDriver == "Firefox":
	firefoxProfile = webdriver.FirefoxProfile(taobaoIndexCrawler.config['firefoxProfile'] )
	binary  = FirefoxBinary( taobaoIndexCrawler.config['webDriverPath']['Firefox'] )
	#不加载profile启动的Firefox将是一个全新的,不安装任何Add-On的Firefox.因此插件无法使用，所以需要制定profile
	BROWSER = webdriver.Firefox(firefox_binary=binary, firefox_profile=firefoxProfile)
	taobaoIndexCrawler.crawlTrendIndex( Raw, BROWSER )
	BROWSER.close()

if __name__=="__main__":
	dbConfigPath     = r"taobaoIndex\DBConfig.json"
	globalConfigPath = r"taobaoIndex\globalConfig.json"
	userConfigPath   = r"taobaoIndex\userConfig.json"
	with open(userConfigPath) as fi:
		userConfig = json.loads( fi.read() )

	for username, userConfig in userConfig.items():
		funcTaobaoIndexCrawl( username, globalConfigPath, userConfigPath, dbConfigPath )

	print "done!"