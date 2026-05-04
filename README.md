**Проект «Аналитика продаж онлайн-маркетплейса»**

Нам доступна информация по API о всех покупках онлайн-маркетплейса с подробной статистикой: http://final-project.simulative.ru/data

API отдает данные только за один день. Дата передается в виде параметра формата yyyy-mm-dd.

Проект содержит: 

1. Скрипт, для единоразового сбора данных по API (run-all.py) для первичного заполнения БД всеми историческми данными.

2. Настройки сервера и процесс разворачивания на нем БД для хранения информации.

3. Скрипт, ежедневно в 7 утра забирающий данные за предыдущий день (run-yesterday.py)

4. Процесс установки Metabase, подключения его к БД и создание дашборда для оперативного отслеживания основных метрик по активности клиентов, ассортиментной матрицы, продажам.

****************************************************************************************************************************************************************************************

**Этапы работы:**

1. Купим виртуальный облачный сервер, получим IP-адрес.
   
2.	Входим на сервер через Putty.
   
3.	Обновим Ubuntu: sudo apt update
   
4.	Установим Python: sudo apt install python3 -y
   
5.	Установим модуль для создания окружений: sudo apt install python3-venv -y
    
6.	Создадим папку для проекта и перейдем в нее: mkdir ~/Diplom && cd ~/Diplom
    
7.	Создадим виртуальное окружение в папке venv: python3 -m venv venv
    
8.	Активируем его: source venv/bin/activate
    
9.	Обновим pip до последней версии: pip install --upgrade pip
    
10.	Установим библиотеки для работы с PostgreSQL и аналитикой прямо в виртуальное окружение: pip install psycopg2-binary pandas numpy sqlalchemy
    
11.	Выйдем из виртуального окружения, установим Postgres: apt install postgresql postgresql-contrib -y
    
12.	Переключимся на пользователя postgres: sudo -i -u postgres
    
13.	Зададим пароль: psql -c "ALTER USER postgres WITH PASSWORD 'strong_password';"
    
14.	Выйдем из пользователя postgres: exit
    
15.	Создадим базу данных: sudo -u postgres createdb sales-info
    
16.	Проверим подключение к БД: psql -h localhost -U postgres -d sales-info -W  и выйдем \q
    
17.	Отредактируем файл настроек postgresql.conf: sudo nano /etc/postgresql/*/main/postgresql.conf  - строку listen_addresses = '*'
    
18.	Отредактируем файл с правилами доступа pg_hba.conf: host all  all  0.0.0.0/0 md5
    
19.	Перезапустим сервер базы данных: sudo systemctl restart postgresql
    
20.	Активируем виртуальное окружение: source venv/bin/activate
    
21.	Установим библиотеку и настроим переменные окружения: pip install python-dotenv,  nano ~/Diplom/.env, укажем свои данные для подключения к БД и ограничим доступ: chmod 600 .env
    
22.	Создадим файлы проекта: config.ini, pgdb.py, run-all.py, run-yesterday.py согласно схеме проекта:
    
<img width="682" height="499" alt="image" src="https://github.com/user-attachments/assets/6c265dfe-1d61-41bc-88aa-d987cc939a22" />


      В файле .env задаются переменные окружения с данными для подключения к БД. Сам файл не передается в GitHub, а только его шаблон.
   
      Файл pgdb.py содержит класс для подключения к БД PGDatabase c функциями подключения к БД Postgres, выполнения SQL-запросов, массовой вставки данных.

23.	Установим библиотеку requests: pip install requests
    
24.	Запустим главный файл проекта: python run-all.py, далее пойдет процесс наполнения БД за все время с логированием.
    
25.	Проверяем наличие таблицы sales и записи в БД sales-info локально через DBeaver – количество записей в логе и БД совпадает.
 
26.	Настроим имя и email для коммитов: git config --global user.name "Ваше Имя" и git config --global user.email "ваша_почта@example.com"
    
27.	Инициализируем Git в папке проекта: git init
    
28.	Создадим .gitignore:
 
29.	Создадим удаленный репозиторий на hithub.com и свяжемся с ним: git remote add origin https://github.com/имя/имя.git
    
30.	Переименуем ветку в main: git branch -M main
    
31.	Добавим файлы: git add .
    
32.	Сделаем первый коммит: git commit -m "Первый коммит: проект для диплома"
    
33.	Отправим на GitHub: git push -u origin main
    
35.	Отредактируем планировщик задач crontab -e: 0 7 * * *  cd /root/Diplom && /root/Diplom/venv/bin/python run-yesterday.py >> /root/Diplom/logs/cron.log 2>&1
 
36.	Проверяем работу скрипта - смотрим логи.
 
37.	Поскольку в sales есть несостыковки – есть записи с purchase_time_as_seconds_from_midnight > =86400 (это уже следующие сутки), то создадим представление (временную таблицу), пересчитываем дату и время (сек)  правильно (добавим новые поля – corrected_date, corrected_seconds) и теперь уже запросы будем делать к таблице sales_corrected с учетом новых полей.

38.	Установим Docker:
    
      sudo apt-get update

      sudo apt-get install ca-certificates curl gnupg, sudo install -m 0755 -d /etc/apt/keyrings 

      curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg, sudo chmod a+r /etc/apt/keyrings/docker.gpg, echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null, sudo apt-get update

      sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

39.	Настроим Metabase: mkdir ~/metabase, cd ~/metabase, nano compose.yml
    
      Заполним файл настроек своими данными и запустим: sudo docker compose up -d
   	
40.	После установки заходим в браузере по адресу http:// http://ip_server/:3000 и настроим Metabase.

41.   Создадим коллекцию и скопируем все SQL-запросы, создадим по нима карточки и внесем в дашборд.
