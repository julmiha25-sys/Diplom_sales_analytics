# -*- coding: utf-8 -*-
# Импорт библиотеки для выполнения HTTP-запросов к API
import requests
import pandas as pd
from datetime import datetime, timedelta
# Импорт библиотеки для чтения настроек из файла config.ini
import configparser
# Импорт библиотеки для подключения к PostgreSQL
from pgdb import PGDatabase
import logging
import os

# Логирование
os.makedirs("/root/Diplom/logs", exist_ok=True)
log_filename = f"/root/Diplom/logs/daily_etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("ЗАПУСК ЕЖЕДНЕВНОГО ETL ПРОЦЕССА")
logger.info(f"Лог файл: {log_filename}")

# Чтение config.ini
config = configparser.ConfigParser()
config.read('config.ini')
DATABASE_CREDS = {
    'HOST': config['Database']['HOST'],
    'DATABASE': config['Database']['DATABASE'],
    'USER': config['Database']['USER'],
    'PASSWORD': config['Database']['PASSWORD']
}

# Функция для получения данных за вчерашний день
def yesterday_date():
    url = "http://final-project.simulative.ru/data"
    # Список с данными
    all_data = []
    # Определение вчерашней даты
    date_str = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)).strftime("%Y-%m-%d")
    logger.info(f"Начало сбора данных за {date_str}")
    try:
        response = requests.get(url, params={"date": date_str}, timeout=30)
        if response.status_code == 200: # Запрос успешен
            try:
                data = response.json()
                if data and len(data) > 0:
                    print(f"  {date_str}: {len(data)} записей")
                    logger.info(f"  {date_str}: {len(data)} записей")
                    # Добавление в список данных
                    all_data.extend(data)
                else:
                    print(f"  {date_str}: Данных нет")
                    logger.info(f"  {date_str}: Данных нет")
            except:
                print(f"  {date_str}: Ошибка парсинга")
                logger.error(f"  {date_str}: Ошибка парсинга")
        else:
            print(f"  {date_str}: Статус {response.status_code}")
            logger.warning(f"  {date_str}: Статус {response.status_code}")
    except Exception as e:
        print(f"  {date_str}: Ошибка - {e}")
        logger.error(f"  {date_str}: Ошибка - {e}")
    # Сохранение в датафрейме списков с данными
    df = pd.DataFrame(all_data)
    print(f"\nВсего собрано записей: {len(df)}")
    logger.info(f"Всего собрано записей: {len(df)}")
    # Сохранение датафрейм с вчерашними данными в csv-файле 
    df.to_csv(f"sales_backup_{date_str}.csv", index=False)
    print(f"Резервная копия сохранена: sales_backup_{date_str}.csv")
    logger.info(f"Резервная копия сохранена: sales_backup_{date_str}.csv")
    return df, date_str

# Функция для загрузки данных в БД
def load_dataframe_to_db(df, database, table_name='sales'):
    # Проверка датафрейма на пустоту
    if df.empty:
        print("DataFrame пуст, загрузка отменена")
        logger.warning("DataFrame пуст, загрузка отменена")
        return
    # Получение списка с названиями колонок
    columns = df.columns.tolist()
    # Соединение их в строку с ,
    columns_str = ', '.join(columns)
    # Создание плейсхолдера - заполнителя для ячейки
    placeholders = ', '.join(['%s'] * len(columns))
    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    # Преобразование датафрейма в список кортежей (каждый — одна строка данных)
    data_tuples = [tuple(row) for row in df.to_numpy()]
    # Вставка всех данных одним запросом - вызов функции массовой вставки данных из pgdb.py
    print(f"Загрузка {len(data_tuples)} строк в таблицу {table_name}...")
    logger.info(f"Загрузка {len(data_tuples)} строк в таблицу {table_name}...")
    try:
        database.post_many(query, data_tuples)
        print(f"Загрузка завершена")
        logger.info(f"Загрузка завершена")
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")
        raise

# Подключение к БД
logger.info("Подключение к БД")
database = PGDatabase(
    host=DATABASE_CREDS['HOST'],
    database=DATABASE_CREDS['DATABASE'],
    user=DATABASE_CREDS['USER'],
    password=DATABASE_CREDS['PASSWORD'],
)
logger.info("Подключение к БД установлено")

# Сбор вчерашних данных
print("Сбор данных за вчерашний день")
logger.info("Начало сбора данных за вчерашний день")
# Вызов функции для получения данных за вчерашний день
df, date_str = yesterday_date()
if date_str:
    print(f"Дата: {date_str}")
    logger.info(f"Дата: {date_str}")

# Проверка: есть ли уже данные за эту дату
logger.info(f"Проверка наличия данных за {date_str} в БД")
# Вызов функции для выполнения SQL-запросов с параметрам из pgdb.py
database.post("SELECT COUNT(*) FROM sales WHERE purchase_datetime = %s", (date_str,))
# Поиск 1-го элемента кортежа - количества записей запроса по вчерашней дате
count = database.cursor.fetchone()[0]

if count > 0:
    print(f"Данные за {date_str} уже есть в БД. Пропускаем.")
    logger.info(f"Данные за {date_str} уже есть в БД. Пропускаем.")
    exit(0)

# Загрузка данных
if not df.empty:
    logger.info(f"Получено {len(df)} строк. Начинаем загрузку в БД...")
    # Вызов функции загрузки данных из датафрейма в БД
    load_dataframe_to_db(df, database, 'sales')
    logger.info(f"Данные за {date_str} успешно загружены")
else:
    print("Нет данных для загрузки")
    logger.warning("Нет данных для загрузки")
logger.info("ЕЖЕДНЕВНЫЙ ETL ПРОЦЕСС ЗАВЕРШЕН")
