# MangaLib Parser
**MangaLib Parser** – это кроссплатформенный скрипт для получения данных с семейства сайтов [MangaLib](https://mangalib.me/), [YaoiLib](https://yaoilib.me/) и [HentaiLib](https://hentailib.me/) в формате JSON. Он позволяет записать всю информацию о конкретной манге, а также её главах и содержании глав. Файлы на выходе совместимы с парсером API сайта [ReManga](https://remanga.org/).
## Порядок установки и использования
1. Установить Python версии не старше 3.9. При установке рекомендуется добавить в PATH.
2. Скачать [Google Chrome](https://www.google.by/intl/ru/chrome/) и установить в директорию по умолчанию.
3. В среду исполнения установить следующие пакеты: webdriver-manager, BeautifulSoup4, Selenium, Pillow, lxml.
```
pip install webdriver-manager
pip install beautifulsoup4
pip install selenium
pip install pillow
pip install lxml
```
4. Настроить скрипт путём редактирования *Settings.json*.
5. Открыть директорию со скриптом в консоли. Можно использовать метод `cd` и прописать путь к папке, либо открыть терминал из проводника.
6. Ввести нужную команду и дождаться завершения. Не сворачивайте браузер, так как это может привести к исключениям области видимости.

**Важно:** Если интервал перелистывания устанавливается на значение менее 5 секунд, рекомендуется использовать VPN наподобие [Psiphon 3](https://www.psiphon3.com/ug%40Latn/download.html), чтобы в случае блокировки по IP не потерять доступ к сайту. 
# Консольные команды
```
mlp scan
```
Получение манифеста из "scan-target" и сохранение в указанную директорию.
____
```
mlp parce [MANGA_SLUG] [FLAGS]
```
Парсинг тайтла, алиас которого передаётся вторым аргументом.

**Пример:** mlp parce dr-stone

Если вместо алиаса передать аргумент _**-all**_, то скрипт по очереди будет обрабатывать все тайтлы из *#Manifest.json*. Для команды также доступен флаг «_**-f**_», включающий перезапись конфликтующих файлов. Без него парсер будет пропускать тайтлы, описанные в JSON.
____
```
mlp update [MANGA_SLUG] [FLAGS]
```
Обновление тайтла, алиас которого передаётся вторым аргументом, путём добавления в него отсутствующих глав и ветвей переводов.

**Пример:** mlp update dr-stone

Если вместо алиаса передать аргумент _**-all**_, то скрипт по очереди будет обрабатывать все тайтлы из рабочей директории.
____
```
mlp ubid [MANGA_SLUG]
```
Выводит уникальный ID манги на основе десятиричного представления MD5 хеш-суммы алиаса. Для тайтлов с несколькими ветвями перевода данное значение может отличаться, потому что в таких случаях к ID ветви добавляется значение _bid_ перевода.

**Пример:** В результате выполнения функции было выведено значение 12345. В файле JSON ветви перевода будут обозначены 12345**678** и 12345**679**, где последняя часть является значением _bid_ из адресной строки главы (https://mangalib.me/manganame/v1/c1?bid=678).
____
```
mlp getsl [CHAPTER_URL]
```
Получает данные о слайдах конкретной главы из переданного URL (можно использовать как полный URL, так и значение из логов). Для этой команды функционируют настройки "_disable-age-limit-warning_" и "_sign-in_". Информация сохраняется в файл _#Slides.json_.

**Примечание:** Полезно, когда в логах вы видите ошибку о неполном парсинге главы. Просто скопируйте URL из лога, подставьте в команду, и на выходе получите полные данные о слайдах для восстановления JSON.
____
```
mlp -s
```
Флаг «_**-s**_» выключает компьютер после завершения работы скрипта. Его можно добавить к любой другой команде.

# Settings.json
```
"domain" : "mangalib"
```
Устанавливает целевой домен, с которого будет происходить парсинг. Поддерживаются значения: _mangalib_, _yaoilib_, _hentailib_.
____
```
"directory" : ""
```
Задаёт рабочую директорию. Сюда будут сохраняться файлы манги, манифест, определения слайдов и отсюда же будут браться список тайтлов для обновления. По умолчанию "\manga".
____
```
"scan-target" : ""
```
Задаёт страницу каталога манги, откуда будет собран манифест. Указать URL страницы с аргументами сортировки. 

**Пример:** "https://mangalib.me/manga-list?page=2&status[]=2". В манифест будут записаны данные о манге со статусом «Завершено», вторая страница каталога.
____
```
"disable-age-limit-warning" : true
```
Переключатель отключения уведомлений о возрастном ограничении. Необходимо для парсинга 16+ и 18+ тайтлов.
____
```
"sign-in" : false,
"email": "",
"password": ""
```
Указывает, проводить ли вход в аккаунт (только через логин и пароль, получить их можно в настройках сайта). Необходимо для парсинга 18+ тайтлов.
____
```
"delay": 5
```
Устанавливает интервал в секундах между загрузкой глав, а также между получением слайдов для уменьшения нагрузки на сервера. Помогает избежать блокировки по IP за быстрые автоматические запросы. 

Рекомендуемое значение: не менее 5 секунд.
____
```
"getting-slide-sizes": false
```
Переключатель, отвечающий за получение размеров слайдов. Без загрузки каждого слайда и его проверки скорость парсинга возрастает в десятки раз, однако определение размеров слайдов становится невозможным, а скрипт перестаёт проверять содержимое слайдов на целостность.
____
```
"old-slide-receiving-mode": false
```
Отвечает за активацию старого режима получения слайдов (методом перелистывания). Менее надёжный способ, который в будущих версиях будет полностью удалён. Не рекомендуется к использованию, однако может пригодиться в редких случаях, пока новые алгоритмы ещё сырые.
____
```
"server": "compress"
```
Устанавливает сервер, для которого будут формироваться ссылки. Работает только для нового режима получения слайдов. Список доступных серверов можно узнать на целевом сайте в JS-переменной `window.__info`. Рекомендуется сервер _compress_ как наиболее стабильный и часто используемый.

Поддерживаются: _main_, _secondary_, _compress_, _fourth_.

*Evolv Group. Copyright © 2018-2022.*
