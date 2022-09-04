from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import json

#=== БАЗОВЫЕ ФУНКЦИИ ===#
from BaseFunctions import DisableAgeLimitWarning
from BaseFunctions import LogIn

#=== ПАРСИНГ ГЛАВ ===#
from BaseFunctions import PrepareToParcingChapter
from BaseFunctions import GetMangaSlidesUrlArray
from BaseFunctions import GetChaptersNames
from BaseFunctions import GetChaptersLinks
from BaseFunctions import MakeContentData
from BaseFunctions import GetMangaData
from BaseFunctions import IsMangaPaid
from BaseFunctions import GetCodeBID
from BaseFunctions import GetBID

#Выполнение, если указано настройками, входа на сайт и отключение уведомления о возрастном ограничении.
def SignInAndDisableWarning(Browser, Settings):
	if Settings["sign-in"] == True:
		if Settings["email"] != "" and Settings["password"] != "":
			LogIn(Browser, Settings)
			logging.info("Sign in as \"" + Settings["email"] + "\".")
		else:
			logging.error("Uncorrect user data! Check \"Settings.json\".")

	if Settings["disable-age-limit-warning"] == True:
		DisableAgeLimitWarning(Browser)
		DisableAgeLimitWarning(Browser, Settings)
		logging.info("Age limit warning disabled.")
		if Settings["sign-in"] == True:
			if Settings["email"] != "" and Settings["password"] != "":
				LogIn(Browser, Settings)
				logging.info("Sign in as \"" + Settings["email"] + "\".")
			else:
				logging.error("Uncorrect user data! Check \"Settings.json\".")

#Парсинг одного тайтла.
def ParceTitle(Browser, MangaName, Settings, ShowProgress):
	#Получение данных о манге.
	JSON = GetMangaData(Browser, MangaName)
	IsPaid = IsMangaPaid(Browser, MangaName)
	JSON = GetMangaData(Browser, MangaName, Settings)
	IsPaid = IsMangaPaid(Browser, MangaName, Settings)
	BranchesCount = len(JSON["branches"])

	#Проверка лицензии.
	if JSON['is_licensed'] == False and IsPaid == False:
		#Получение BID веток.
		BIDs = None
		if BranchesCount > 1:
			BIDs = GetBID(Browser, MangaName, BranchesCount)
			BIDs = GetBID(Browser, MangaName, Settings)
		logging.info("Parcing: \"" + MangaName + "\". Branches count: " + str(BranchesCount) + ".")
		#Если не лицензировано, парсить каждую ветку.
		for i in range(0, len(JSON["branches"])):
			BID = ""
			BIDlog = "none"
			if BIDs is None:
				PrepareToParcingChapter(Browser, MangaName, JSON['age_limit'], BIDs)
				PrepareToParcingChapter(Browser, MangaName, Settings, BIDs)
			else:
				#Перезапись ID ветви с использованием BID, если ветвей много.
				JSON["branches"][i]["id"] = GetCodeBID(MangaName, str(BIDs[i]))

				PrepareToParcingChapter(Browser, MangaName, JSON['age_limit'], BIDs[i])
				PrepareToParcingChapter(Browser, MangaName, Settings, BIDs[i])
				BID = "?bid=" + str(BIDs[i])
				BIDlog = str(BIDs[i])
			ChaptersNames = GetChaptersNames(Browser)
			ChaptersLinks = GetChaptersLinks(Browser)
			logging.info("Parcing: \"" + MangaName + "\". Branch ID: " + BIDlog + ". Chapters in branch: " + str(len(ChaptersLinks)) + ".")
			if BIDs is None:
				JSON["content"][GetCodeBID(MangaName, "")] = MakeContentData(ChaptersNames, ChaptersLinks, BID, Browser, Settings, ShowProgress)
			else:
				JSON["content"][GetCodeBID(MangaName, str(BIDs[i]))] = MakeContentData(ChaptersNames, ChaptersLinks, BID, Browser, Settings, ShowProgress)
	#Если лицензировано, ничего больше не парсить и вывести уведомление.
	elif JSON['is_licensed'] == True:
		logging.info("Parcing: \"" + MangaName + "\". Licensed. Skipped.")
	elif IsPaid == True:
		logging.info("Parcing: \"" + MangaName + "\". Is paid. Skipped.")
	
	with open(Settings["save-directory"] + "\\" + MangaName + ".json", "w", encoding = "utf-8") as FileWrite:
		json.dump(JSON, FileWrite, ensure_ascii = False, indent = 2, separators = (',', ': '))
		logging.info("Parcing: \"" + MangaName + "\". JSON file was created.")
	logging.info("Parcing: \"" + MangaName + "\". SUCCESSFULL!!!")

#Сканирование страницы каталога и получение списка тайтлов.
def ScanTitles(Browser, Settings):
	Browser.get(Settings["scan-target"])
	BodyHTML = Browser.execute_script("return document.body.innerHTML;")
	Soup = BeautifulSoup(BodyHTML, "lxml")
	MediaCards = Soup.find_all('a', {'class': 'media-card'})
	TitlesAliasArray = []

	for i in range(0, len(MediaCards)):
		TitlesAliasArray.append(str(MediaCards[i]["href"]).split('/')[3])

	with open(Settings["save-directory"] + "\\#Manifest.json", "w", encoding = "utf-8") as FileWrite:
		json.dump(TitlesAliasArray, FileWrite, ensure_ascii = False, indent = 2, separators = (',', ': '))
		logging.info("Manifest file was created. Scanning SUCCESSFULL!!!")

#Парсинг одной главы. Помогает исправлять записи с отсутствующими слайдами.
#Получение данных о слайдах одной главы и запись в JSON. Помогает исправлять записи с отсутствующими слайдами.
def GetChapterSlidesInJSON(Browser, ChapterURL, Settings):
	ChapterURL = ChapterURL.replace("https://mangalib.me", "")
	ChapterURL = ChapterURL.replace(Settings["domain"][:-1], "")
	ChapterURL = ChapterURL.split('?')[0]
	SlidesInfo = GetMangaSlidesUrlArray(Browser, ChapterURL, Settings)

	with open(Settings["save-directory"] + "\\#ChapterSlides.json", "w", encoding = "utf-8") as FileWrite:
	with open(Settings["save-directory"] + "\\#Slides.json", "w", encoding = "utf-8") as FileWrite:
		json.dump(SlidesInfo, FileWrite, ensure_ascii = False, indent = 2, separators = (',', ': '))
		logging.info("Chapter slides info file was created SUCCESSFULL!!!")
		logging.info("Chapter slides info file was created. SUCCESSFULL!!!")







