from Source.Core.Formats.Manga import BaseStructs, Manga, Statuses, Types
from Source.Core.ParserSettings import ParserSettings
from Source.Core.Downloader import Downloader
from Source.Core.Objects import Objects
from Source.CLI.Templates import *

from dublib.WebRequestor import Protocols, WebConfig, WebLibs, WebRequestor
from dublib.Methods.Data import RemoveRecurringSubstrings, Zerotify
from dublib.Methods.JSON import ReadJSON
from datetime import datetime
from time import sleep

#==========================================================================================#
# >>>>> ОПРЕДЕЛЕНИЯ <<<<< #
#==========================================================================================#

VERSION = "3.0.0"
REPOS = "https://github.com/DUB1401/mangalib"
NAME = "mangalib"
SITE = "test-front.mangalib.me"
STRUCT = Manga()

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class Parser:
	"""Модульный парсер."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА ТОЛЬКО ДЛЯ ЧТЕНИЯ <<<<< #
	#==========================================================================================#

	@property
	def site(self) -> str:
		"""Домен целевого сайта."""

		return self.__Title["site"]

	@property
	def id(self) -> int:
		"""Целочисленный идентификатор."""

		return self.__Title["id"]

	@property
	def slug(self) -> str:
		"""Алиас."""

		return self.__Title["slug"]

	@property
	def content_language(self) -> str | None:
		"""Код языка контента по стандарту ISO 639-3."""

		return self.__Title["content_language"]

	@property
	def localized_name(self) -> str | None:
		"""Локализованное название."""

		return self.__Title["localized_name"]

	@property
	def en_name(self) -> str | None:
		"""Название на английском."""

		return self.__Title["en_name"]

	@property
	def another_names(self) -> list[str]:
		"""Список альтернативных названий."""

		return self.__Title["another_names"]

	@property
	def covers(self) -> list[dict]:
		"""Список описаний обложки."""

		return self.__Title["covers"]

	@property
	def authors(self) -> list[str]:
		"""Список авторов."""

		return self.__Title["authors"]

	@property
	def publication_year(self) -> int | None:
		"""Год публикации."""

		return self.__Title["publication_year"]

	@property
	def description(self) -> str | None:
		"""Описание."""

		return self.__Title["description"]

	@property
	def age_limit(self) -> int | None:
		"""Возрастное ограничение."""

		return self.__Title["age_limit"]

	@property
	def genres(self) -> list[str]:
		"""Список жанров."""

		return self.__Title["genres"]

	@property
	def tags(self) -> list[str]:
		"""Список тегов."""

		return self.__Title["tags"]

	@property
	def franchises(self) -> list[str]:
		"""Список франшиз."""

		return self.__Title["franchises"]

	@property
	def type(self) -> Types | None:
		"""Тип тайтла."""

		return self.__Title["type"]

	@property
	def status(self) -> Statuses | None:
		"""Статус тайтла."""

		return self.__Title["status"]

	@property
	def is_licensed(self) -> bool | None:
		"""Состояние: лицензирован ли тайтл на данном ресурсе."""

		return self.__Title["is_licensed"]

	@property
	def content(self) -> dict:
		"""Содержимое тайтла."""

		return self.__Title["content"]

	#==========================================================================================#
	# >>>>> СТАНДАРТНЫЕ ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __CalculateEmptyChapters(self, content: dict) -> int:
		"""Подсчитывает количество глав без слайдов."""

		# Количество глав.
		ChaptersCount = 0

		# Для каждой ветви.
		for BranchID in content.keys():

			# Для каждой главы.
			for Chapter in content[BranchID]:
				# Если глава не содержит слайдов, подсчитать её.
				if not Chapter["slides"]: ChaptersCount += 1

		return ChaptersCount

	def __InitializeRequestor(self) -> WebRequestor:
		"""Инициализирует модуль WEB-запросов."""

		# Инициализация и настройка объекта.
		Config = WebConfig()
		Config.select_lib(WebLibs.requests)
		Config.generate_user_agent("pc")
		Config.set_tries_count(self.__Settings.common.tries)
		Config.add_header("Authorization", self.__Settings.custom["token"])
		WebRequestorObject = WebRequestor(Config)
		
		# Установка прокси.
		if self.__Settings.proxy.enable: WebRequestorObject.add_proxy(
			Protocols.HTTP,
			host = self.__Settings.proxy.host,
			port = self.__Settings.proxy.port,
			login = self.__Settings.proxy.login,
			password = self.__Settings.proxy.password
		)

		return WebRequestorObject

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ ЗАГРУЗКИ ИЗОБРАЖЕНИЙ <<<<< #
	#==========================================================================================#

	def __IsSlideLink(self, link: str, servers: list[str]) -> bool:
		"""
		Проверяет, ведёт ли ссылка на слайд.
			link – ссылка на изображение;
			servers – список серверов изображений.
		"""

		# Для каждого сервера.
		for Server in servers:
			# Если ссылка содержит домен сервера изображений, считать проверку успешной.
			if Server in link: return True

		return False
	
	def __ParseSlideLink(self, link: str, servers: list[str]) -> tuple[str]:
		"""
		Парсит ссылку на слайд.
			link – ссылка на изображение;
			servers – список серверов изображений.
		"""

		# Оригинальный сервер и URI слайда.
		OriginalServer = None
		URI = None

		# Для каждого сервера.
		for Server in servers:

			# Если ссылка содержит домен сервера изображений.
			if Server in link:
				# Запись оригинального сервера и  получение URI.
				OriginalServer = Server
				URI = link.replace(OriginalServer, "")

		return (OriginalServer, URI)

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ ПАРСИНГА <<<<< #
	#==========================================================================================#

	def __GetAgeLimit(self, data: dict) -> int:
		"""
		Получает возрастной рейтинг.
			data – словарь данных тайтла.
		"""

		# Возрастной рейтинг.
		Rating = None
		# Строковое представление.
		RatingString = data["ageRestriction"]["label"].split(" ")[0].replace("+", "").replace("Нет", "")
		# Если строковое представление состоит из цифр, конвертировать в число.
		if RatingString.isdigit(): Rating = int(RatingString)

		return Rating 

	def __GetAuthors(self, data: dict) -> list[str]:
		"""Получает список авторов."""

		# Список авторов.
		Authors = list()
		# Для каждого автора записать имя.
		for Author in data["authors"]: Authors.append(Author["name"])

		return Authors

	def __GetContent(self) -> dict:
		"""Получает содержимое тайтла."""

		# Структура содержимого.
		Content = dict()
		# Запрос содержимого.
		Response = self.__Requestor.get(f"https://api.lib.social/api/manga/{self.__Slug}/chapters")
		
		# Если запрос успешен.
		if Response.status_code == 200:
			# Парсинг данных в JSON.
			Data = Response.json["data"]
			# Выжидание интервала.
			sleep(self.__Settings.common.delay)

			# Для каждой главы.
			for Chapter in Data:

				# Для каждой ветви.
				for BranchData in Chapter["branches"]:
					# ID ветви.
					BranchID = str(BranchData["branch_id"])
					# Если ветвь не определена, синтезировать новую добавлением нуля к ID тайтла.
					if BranchID == "None": BranchID = str(self.__Title["id"]) + "0"
					# Если ветвь не существует, создать её.
					if BranchID not in Content.keys(): Content[BranchID] = list()
					# Переводчики.
					Translators = [sub["name"] for sub in BranchData["teams"]]
					# Буфер главы.
					Buffer = {
						"id": BranchData["id"],
						"volume": Chapter["volume"],
						"number": Chapter["number"],
						"name": Zerotify(Chapter["name"]),
						"is_paid": False,
						"translators": Translators,
						"slides": []	
					}
					# Запись главы.
					Content[BranchID].append(Buffer)

		else:
			# Запись в лог ошибки.
			self.__SystemObjects.logger.request_error(Response, "Unable to request chapter.")

		return Content

	def __GetCovers(self, data: dict) -> list[str]:
		"""Получает список обложек."""

		# Список обложек.
		Covers = list()

		# Если обложка присутствует.
		if data["cover"]:
			# Дополнение структуры.
			Covers.append({
				"link": data["cover"]["default"],
				"filename": data["cover"]["default"].split("/")[-1]
			})

		# Если включен режим получения размеров обложек.
		if self.__Settings.common.sizing_images:
			# Дополнение структуры размерами.
			Covers[0]["width"] = None
			Covers[0]["height"] = None

		return Covers

	def __GetDescription(self, data: dict) -> str | None:
		"""
		Получает описание.
			data – словарь данных тайтла.
		"""

		# Описание.
		Description = None
		# Если присутствует описание, записать его и отформатировать.
		if "summary" in data.keys(): Description = RemoveRecurringSubstrings(data["summary"], "\n").strip().replace(" \n", "\n")
		# Обнуление пустого описания.
		Description = Zerotify(Description)

		return Description

	def __GetFranchises(self, data: dict) -> list[str]:
		"""
		Получает список серий.
			data – словарь данных тайтла.
		"""

		# Франшизы.
		Franchises = list()
		# Для каждой франшизы записать название.
		for Franchise in data["franchise"]: Franchises.append(Franchise["name"])
		# Удаление оригинальных работ.
		if "Оригинальные работы" in Franchises: Franchises.remove("Оригинальные работы")

		return Franchises

	def __GetGenres(self, data: dict) -> list[str]:
		"""
		Получает список жанров.
			data – словарь данных тайтла.
		"""

		# Описание.
		Genres = list()
		# Для каждого жанра записать имя.
		for Genre in data["genres"]: Genres.append(Genre["name"])

		return Genres

	def __GetImagesServers(self, server_id: str | None = None, all_sites: bool = False) -> list[str]:
		"""
		Возвращает один или несколько доменов серверов хранения изображений.
			server_id – идентификатор сервера;\n
			all_sites – указывает, что вернуть нужно домены хранилищ изображений для всех сайтов.
		"""

		# Список серверов.
		Servers = list()
		# ID текущего сайта.
		CurrentSiteID = self.__GetSiteID()
		# Адрес запроса.
		URL = f"https://api.lib.social/api/constants?fields[]=imageServers"
		# Заголовки запроса.
		Headers = {
			"Authorization": self.__Settings.custom["token"],
			"Referer": f"https://{SITE}/"
		}
		# Запрос серверных констант.
		Response = self.__Requestor.get(URL, headers = Headers)

		# Если запрос успешен.
		if Response.status_code == 200:
			# Парсинг данных в JSON.
			Data = Response.json["data"]["imageServers"]
			# Выжидание интервала.
			sleep(self.__Settings.common.delay)

			# Для каждого сервера.
			for ServerData in Data:

				# Если задан ID сервера.
				if server_id:
					# Если сервер поддерживает текущий домен, записать его URL.
					if ServerData["id"] == server_id and CurrentSiteID in ServerData["site_ids"]: Servers.append(ServerData["url"])
					elif ServerData["id"] == server_id and all_sites: Servers.append(ServerData["url"])

				else:
					# Если сервер поддерживает текущий домен, записать его URL.
					if CurrentSiteID in ServerData["site_ids"] or all_sites: Servers.append(ServerData["url"])

		else:
			# Запись в лог ошибки.
			self.__SystemObjects.logger.request_error(Response, "Unable to request site constants.")

		return Servers

	def __GetSiteID(self) -> int:
		"""Возвращает целочисленный идентификатор сайта."""

		# ID сайта.
		SiteID = None
		# Проверка соответствий.
		if "mangalib" in SITE: SiteID = 1
		if "yaoilib" in SITE or "slashlib" in SITE: SiteID = 2
		if "hentailib" in SITE: SiteID = 4
		
		return SiteID

	def __GetSlides(self, number: str, volume: str, branch_id: str) -> list[dict]:
		"""
		Получает данные о слайдах главы.
			number – номер главы;\n
			volume – номер тома;\n
			branch_id – ID ветви.
		"""

		# Список слайдов.
		Slides = list()
		# Получение домена сервера хранения слайдов.
		Server = self.__GetImagesServers(self.__Settings.custom["server"])[0]
		# Модификатор запроса ветви.
		Branch = "" if branch_id == str(self.__Title["id"]) + "0" else f"&branch_id={branch_id}"
		# Адрес запроса.
		URL = f"https://api.lib.social/api/manga/{self.__Slug}/chapter?number={number}&volume={volume}{Branch}"
		# Заголовки запроса.
		Headers = {
			"Authorization": self.__Settings.custom["token"],
			"Referer": f"https://{SITE}/"
		}
		# Запрос слайдов.
		Response = self.__Requestor.get(URL, headers = Headers)
		
		# Если запрос успешен.
		if Response.status_code == 200:
			# Парсинг данных в JSON.
			Data = Response.json["data"]["pages"]
			# Выжидание интервала.
			sleep(self.__Settings.common.delay)

			# Для каждого слайда.
			for SlideIndex in range(len(Data)):
				# Буфер слайда.
				Buffer = {
					"index": SlideIndex + 1,
					"link": Server + Data[SlideIndex]["url"].replace(" ", "%20")
				}

				# Если включен режим получения размеров обложек.
				if self.__Settings.common.sizing_images:
					# Дополнение структуры размерами.
					Buffer["width"] = Data[SlideIndex]["width"]
					Buffer["height"] = Data[SlideIndex]["height"]

				# Запись слайда. 
				Slides.append(Buffer)

		else:
			# Запись в лог ошибки.
			self.__SystemObjects.logger.request_error(Response, "Unable to request chapter content.")

		return Slides

	def __GetStatus(self, data: dict) -> str:
		"""
		Получает статус.
			data – словарь данных тайтла.
		"""

		# Статус тайтла.
		Status = None
		# Статусы тайтлов.
		StatusesDetermination = {
			1: Statuses.ongoing,
			2: Statuses.completed,
			3: Statuses.announced,
			4: Statuses.dropped,
			5: Statuses.dropped
		}
		# Индекс статуса на сайте.
		SiteStatusIndex = data["status"]["id"]
		# Если индекс статуса валиден, преобразовать его в поддерживаемый статус.
		if SiteStatusIndex in StatusesDetermination.keys(): Status = StatusesDetermination[SiteStatusIndex]

		return Status

	def __GetTitleData(self) -> dict | None:
		"""
		Получает данные тайтла.
			slug – алиас.
		"""

		# Адрес запроса.
		URL = f"https://api.lib.social/api/manga/{self.__Slug}?fields[]=eng_name&fields[]=otherNames&fields[]=summary&fields[]=releaseDate&fields[]=type_id&fields[]=caution&fields[]=genres&fields[]=tags&fields[]=franchise&fields[]=authors&fields[]=manga_status_id&fields[]=status_id"
		# Заголовки запроса.
		Headers = {
			"Authorization": self.__Settings.custom["token"],
			"Referer": f"https://{SITE}/"
		}
		# Выполнение запроса.
		Response = self.__Requestor.get(URL, headers = Headers)

		# Если запрос успешен.
		if Response.status_code == 200:
			# Парсинг ответа.
			Response = Response.json["data"]
			# Запись в лог информации: начало парсинга.
			self.__SystemObjects.logger.parsing_start(self.__Slug, Response["id"])
			# Выжидание интервала.
			sleep(self.__Settings.common.delay)

		else:
			# Запись в лог ошибки.
			self.__SystemObjects.logger.request_error(Response, "Unable to request title data.")
			# Обнуление ответа.
			Response = None

		return Response

	def __GetTags(self, data: dict) -> list[str]:
		"""
		Получает список тегов.
			data – словарь данных тайтла.
		"""

		# Описание.
		Tags = list()
		# Для каждого тега записать имя.
		for Tag in data["tags"]: Tags.append(Tag["name"])

		return Tags

	def __GetType(self, data: dict) -> str:
		"""
		Получает тип тайтла.
			data – словарь данных тайтла.
		"""

		# Тип тайтла.
		Type = None
		# Типы тайтлов.
		TypesDeterminations = {
			"Манга": Types.manga,
			"Манхва": Types.manhwa,
			"Маньхуа": Types.manhua,
			"Руманга": Types.russian_comic,
			"Комикс западный": Types.western_comic,
			"OEL-манга": Types.oel
		}
		# Определение с сайта.
		SiteType = data["type"]["label"]
		# Если определение с сайта валидно, преобразовать его.
		if SiteType in TypesDeterminations.keys(): Type = TypesDeterminations[SiteType]

		return Type

	def __StringToDate(self, date_str: str) -> datetime:
		"""
		Преобразует строковое время в объектную реализацию.
			date_str – строковая интерпретация.
		"""

		# Шаблон строки.
		DatePattern = "%Y-%m-%dT%H:%M:%S.%fZ"

		return datetime.strptime(date_str, DatePattern)

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: Objects, settings: ParserSettings):
		"""
		Модульный парсер.
			system_objects – коллекция системных объектов;\n
			settings – настройки парсера.
		"""

		# Выбор парсера для системы логгирования.
		system_objects.logger.select_parser(NAME)

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Настройки парсера.
		self.__Settings = settings
		# Менеджер WEB-запросов.
		self.__Requestor = self.__InitializeRequestor()
		# Структура данных.
		self.__Title = None
		# Алиас тайтла.
		self.__Slug = None
		# Коллекция системных объектов.
		self.__SystemObjects = system_objects

	def amend(self, content: dict | None = None, message: str = "") -> dict:
		"""
		Дополняет каждую главу в кажой ветви информацией о содержимом.
			content – содержимое тайтла для дополнения;\n
			message – сообщение для портов CLI.
		"""

		# Если содержимое не указано, использовать текущее.
		if content == None: content = self.content
		# Подсчёт количества глав для дополнения.
		ChaptersToAmendCount = self.__CalculateEmptyChapters(content)
		# Количество дополненных глав.
		AmendedChaptersCount = 0
		# Индекс прогресса.
		ProgressIndex = 0

		# Для каждой ветви.
		for BranchID in content.keys():
			
			# Для каждый главы.
			for ChapterIndex in range(0, len(content[BranchID])):
				
				# Если слайды не описаны или включён режим перезаписи.
				if content[BranchID][ChapterIndex]["slides"] == []:
					# Инкремент прогресса.
					ProgressIndex += 1
					# Получение списка слайдов главы.
					Slides = self.__GetSlides(
						content[BranchID][ChapterIndex]["number"],
						content[BranchID][ChapterIndex]["volume"],
						BranchID
					)

					# Если получены слайды.
					if Slides:
						# Инкремент количества дополненных глав.
						AmendedChaptersCount += 1
						# Запись информации о слайде.
						content[BranchID][ChapterIndex]["slides"] = Slides
						# Запись в лог информации: глава дополнена.
						self.__SystemObjects.logger.chapter_amended(self.__Slug, self.__Title["id"], content[BranchID][ChapterIndex]["id"], False)

					# Вывод в консоль: прогресс дополнения.
					PrintAmendingProgress(message, ProgressIndex, ChaptersToAmendCount)
					# Выжидание интервала.
					sleep(self.__Settings.common.delay)

		# Запись в лог информации: количество дополненных глав.
		self.__SystemObjects.logger.amending_end(self.__Slug, self.__Title["id"], AmendedChaptersCount)

		return content

	def image(self, url: str) -> str | None:
		"""
		Скачивает изображение с сайта во временный каталог парсера и возвращает его название.
			url – ссылка на изображение.
		Возвращает название файла.
		"""

		# Инициализация загрузчика.
		Config = WebConfig()
		Config.select_lib(WebLibs.requests)
		Config.requests.enable_proxy_protocol_switching(True)
		WebRequestorObject = WebRequestor(Config)

		# Установка прокси.
		if self.__Settings.proxy.enable: WebRequestorObject.add_proxy(
			Protocols.HTTP,
			host = self.__Settings.proxy.host,
			port = self.__Settings.proxy.port,
			login = self.__Settings.proxy.login,
			password = self.__Settings.proxy.password
		)

		# Загрузка изображения во временную директорию.
		Result = Downloader(self.__SystemObjects, WebRequestorObject).temp_image(NAME, url, referer = SITE)
		
		# Если загрузка не удалась.
		if Result.code not in Config.good_statusses:
			# Получение списка доступных серверов.
			Servers = self.__GetImagesServers(all_sites = True)

			# Если загружался слайд.
			if self.__IsSlideLink(url, Servers):
				# Оригинальный сервер и URI слайда.
				OriginalServer, ImageURI = self.__ParseSlideLink(url, Servers)
				# Удаление оригинального сервера из списка доступных.
				Servers.remove(OriginalServer)
				# Выжидание интервала.
				sleep(self.__Settings.common.delay)

				# Для каждого оставшегося сервера.
				for Server in Servers:
					# Составление новой ссылки.
					Link = Server + ImageURI
					# Загрузка изображения во временную директорию.
					Result = Downloader(self.__SystemObjects, WebRequestorObject).temp_image(NAME, Link, referer = SITE)
					
					# Если запрос успешен.
					if Result.code in Config.good_statusses:
						# Прерывание цикла.
						break

					# Если попытка не последняя.
					elif Server != Servers[-1]:
						# Выжидание интервала.
						sleep(self.__Settings.common.delay)

		return Result.value

	def parse(self, slug: str, message: str | None = None):
		"""
		Получает основные данные тайтла.
			slug – алиас тайтла, использующийся для идентификации оного в адресе;\n
			message – сообщение для портов CLI.
		"""

		# Преобразование сообщения в строку.
		message = message or ""
		# Заполнение базовых данных.
		self.__Title = BaseStructs().manga
		self.__Slug = slug
		# Вывод в консоль: статус парсинга.
		PrintParsingStatus(message)
		# Получение описания.
		Data = self.__GetTitleData()
		# Занесение данных.
		self.__Title["site"] = SITE.replace("test-front.", "")
		self.__Title["id"] = Data["id"]
		self.__Title["slug"] = slug
		self.__Title["content_language"] = "rus"
		self.__Title["localized_name"] = Data["rus_name"]
		self.__Title["en_name"] = Data["eng_name"]
		self.__Title["another_names"] = Data["otherNames"]
		self.__Title["covers"] = self.__GetCovers(Data)
		self.__Title["authors"] = self.__GetAuthors(Data)
		self.__Title["publication_year"] = int(Data["releaseDate"]) if Data["releaseDate"] else None
		self.__Title["description"] = self.__GetDescription(Data)
		self.__Title["age_limit"] = self.__GetAgeLimit(Data)
		self.__Title["type"] = self.__GetType(Data)
		self.__Title["status"] = self.__GetStatus(Data)
		self.__Title["is_licensed"] = Data["is_licensed"]
		self.__Title["genres"] = self.__GetGenres(Data)
		self.__Title["tags"] = self.__GetTags(Data)
		self.__Title["franchises"] = self.__GetFranchises(Data)
		self.__Title["content"] = self.__GetContent()
		# Если главное название нигде не указано, добавить его в список альтернативных.
		if Data["name"] not in self.__Title["another_names"] and Data["name"] != self.__Title["another_names"] and Data["name"] != self.__Title["another_names"]: self.__Title["another_names"].append(Data["name"])

	def repair(self, content: dict, chapter_id: int) -> dict:
		"""
		Заново получает данные слайдов главы главы.
			content – содержимое тайтла;\n
			chapter_id – идентификатор главы.
		"""

		# Для каждой ветви.
		for BranchID in content.keys():
			
			# Для каждый главы.
			for ChapterIndex in range(len(content[BranchID])):
				
				# Если ID совпадает с искомым.
				if content[BranchID][ChapterIndex]["id"] == chapter_id:
					# Получение списка слайдов главы.
					Slides = self.__GetSlides(
						content[BranchID][ChapterIndex]["number"],
						content[BranchID][ChapterIndex]["volume"],
						BranchID
					)
					# Запись в лог информации: глава восстановлена.
					self.__SystemObjects.logger.chapter_repaired(self.__Slug, self.__Title["id"], chapter_id, content[BranchID][ChapterIndex]["is_paid"])
					# Запись восстановленной главы.
					content[BranchID][ChapterIndex]["slides"] = Slides

		return content
	
	def updates(self, hours: int) -> list[str]:
		"""
		Возвращает список алиасов тайтлов, обновлённых на сервере за указанный период времени.
			hours – количество часов, составляющих период для получения обновлений.
		"""

		# Список алиасов.
		Updates = list()
		# Состояние: достигнут ли конец проверяемого диапазона.
		IsUpdatePeriodOut = False
		# Счётчик страницы.
		Page = 1
		# Количество обновлённых тайтлов.
		UpdatesCount = 0
		# Заголовки.
		Headers = {
			"Site-Id": str(self.__GetSiteID())
		}
		# Текущая дата.
		CurrentDate = datetime.utcnow()

		# Проверка обновлений за указанный промежуток времени.
		while not IsUpdatePeriodOut:
			# Выполнение запроса.
			Response = self.__Requestor.get(f"https://api.lib.social/api/latest-updates?page={Page}", headers = Headers)
			
			# Если запрос успешен.
			if Response.status_code == 200:
				# Парсинг ответа.
				UpdatesPage = Response.json["data"]

				# Для каждой записи об обновлении.
				for UpdateNote in UpdatesPage:
					# Вычисление временной разницы между текущим моментом и временем публикации.
					Delta = CurrentDate - self.__StringToDate(UpdateNote["last_item_at"])
					
					# Если запись не выходит за пределы интервала.
					if Delta.total_seconds() / 3600 <= hours:
						# Сохранение алиаса обновлённого тайтла.
						Updates.append(UpdateNote["slug"])
						# Инкремент обновлённых тайтлов.
						UpdatesCount += 1

					else:
						# Завершение цикла обновления.
						IsUpdatePeriodOut = True

			else:
				# Завершение цикла обновления.
				IsUpdatePeriodOut = True
				# Запись в лог ошибки.
				self.__SystemObjects.logger.request_error(Response, f"Unable to request updates page {Page}.")

			# Если не все обновления получены.
			if not IsUpdatePeriodOut:
				# Инкремент страницы.
				Page += 1
				# Выжидание указанного интервала.
				sleep(self.__Settings.common.delay)

		# Запись в лог информации: количество собранных обновлений.
		self.__SystemObjects.logger.updates_collected(len(Updates))

		return Updates