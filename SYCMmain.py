#-*- encoding: utf-8 -*-
__author__ = 'XuWeitao'

from SYCMCrawler import BusinessStaffCrawler
from PythonRawMysql import Mysql
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import json

def funcSycmCrawl( UserName, ConfigPath, UserConfigPath, DBConfigPath, initial=0 ):
	BSC     = BusinessStaffCrawler( username=UserName,
	                               configPath=ConfigPath,
	                               userConfigPath=UserConfigPath)
	Raw     = Mysql.RawMysql(db=BSC.userconfig['db'],dbConfig=DBConfigPath)
	#注意此处的profiles是Administor的profile，如果执行脚本的权限不够会出发shutil.Error，找不到文件的错误
	#if BSC.webDriver == "Firefox":
	firefoxProfile = webdriver.FirefoxProfile(BSC.config['firefoxProfile'] )
	binary  = FirefoxBinary( BSC.config['webDriverPath']['Firefox'] )
	#不加载profile启动的Firefox将是一个全新的,不安装任何Add-On的Firefox.因此插件无法使用，所以需要制定profile
	BROWSER = webdriver.Firefox(firefox_binary=binary, firefox_profile=firefoxProfile)
	BSC.crawlRawFactDataToMySQL( BROWSER, Raw, initial )
	BROWSER.close()


if __name__ == "__main__":
	#==========================
	#配置信息路径输入
	userConfigPath   = r"SYCMCrawler/userConfigure.json" #用户配置信息的路径
	globalConfigPath = r"SYCMCrawler/configure.json"     #全局配置信息的路径，包括爬虫的爬取对象的配置，浏览器的安装路径等等
	dbConfigPath     = r"SYCMCrawler/DBconfigure.json"   #数据库配置信息的路径
	#==========================

	with open(userConfigPath) as fi:
		userConfig = json.loads( fi.read(), encoding="utf8" )

	with open(globalConfigPath) as fi:
		globalConfig             = json.loads( fi.read(), encoding="utf8" )
		usersIWantToCrawlOnly    = globalConfig["usersIWantToCrawlOnly"] #如果只想爬个别商家，把个别商家的用户名添加进入到这个列表中，以逗号隔开，每一个字符串冒号前要一个小写的u,如（u"商户名称"）加其余代码不变
		usersNeedToBeInitialized = globalConfig["usersNeedToBeInitialized"] #如果想初始化某个用户（爬一个月以内的数据），需要把该用户的用户名添加进这个列表中，以逗号隔开，其他代码不变

	#注意如果不想只爬个别商家，需要清空掉以上的usersIWantToCrawlOnly列表内容
	#如果没有商家需要初始化，同样也需要清空usersNeedToBeInitialized列表内容



	if len(usersIWantToCrawlOnly) != 0:
		for username in usersIWantToCrawlOnly:
			INITIAL = 0             #不需要初始化标识
			if username in usersNeedToBeInitialized:
				INITIAL = 1         #初始化标识
			funcSycmCrawl( username, globalConfigPath, userConfigPath, dbConfigPath, INITIAL )
	else:
		for username, config in userConfig.items():
			INITIAL = 0
			if username in usersNeedToBeInitialized:
				INITIAL = 1
			funcSycmCrawl( username, globalConfigPath, userConfigPath, dbConfigPath, INITIAL )


