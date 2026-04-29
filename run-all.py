# -*- coding: utf-8 -*-
# Импорт библиотеки для выполнения HTTP-запросов к API
import requests
import pandas as pd
from datetime import datetime, timedelta
# Импорт библиотеки для чтения настроек из файла config.ini
import configparser
# Импорт своей локальной библиотеки для подключения к PostgreSQL из файла pgdb.py
from pgdb import PGDatabase
import logging
import os

# Настройки логирования
os.makedirs("/root/Diplom/logs", exist_ok=True)
log_filename = f"/root/Diplom/logs/etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info("ЗАПУСК ETL ПРОЦЕССА")
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

# Функция для единоразового накопления истории
def find_old_date():
    url = "http://final-project.simulative.ru/data"
    # Начинаем с сегодняшнего дня в обратном порядке
    current = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    oldest_date = None
    # Список данных
    all_data = []
    while True:
        date_str = current.strftime("%Y-%m-%d")
        try:
            response = requests.get(url, params={"date": date_str}, timeout=10)
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data and len(data) > 0:
                        oldest_date = current
                        print(f"  {date_str}: {len(data)} записей")
                        logger.info(f"  {date_str}: {len(data)} записей")
                        # Добавление в список с данными - данные за сутки
                        all_data.extend(data)
                        # Переход к предыдущей дате
                        current -= timedelta(days=1)
                    else:
                        # В случае отсутствия данных - стоп
                        print(f"  {date_str}: Данных нет")
                        logger.info(f"  {date_str}: Данных нет, останавливаемся")
                        break
                except:
                    print(f"  {date_str}: Ошибка парсинга")
                    logger.error(f"  {date_str}: Ошибка парсинга")
                    break
            else:
                print(f"  {date_str}: Статус {response.status_code}")
                logger.warning(f"  {date_str}: Статус {response.status_code}")
                break
        except Exception as e:
            print(f"  {date_str}: Ошибка - {e}")
            logger.error(f"  {date_str}: Ошибка - {e}")
            break
    df = pd.DataFrame(all_data)
    print(f"\nВсего собрано записей: {len(df)}")
    logger.info(f"Всего собрано записей: {len(df)}")
    return oldest_date, df

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
    # Вставка всех данных одним запросом
    print(f"Загрузка {len(data_tuples)} строк в таблицу {table_name}...")
    logger.info(f"Загрузка {len(data_tuples)} строк в таблицу {table_name}...")
    try:
        database.post_many(query, data_tuples)
        print(f"Загрузка завершена")
        logger.info(f"Загрузка завершена")
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")
        raise

# Функция для первоначального создания таблицы 
def create_table(database, df, table_name='sales'):
    # Маппинг типов данных pandas
    dtype_mapping = {
        'int64': 'INTEGER',
        'float64': 'FLOAT',
        'object': 'TEXT',
        'datetime64[ns]': 'TIMESTAMP',
        'bool': 'BOOLEAN'
    }
    # Создание колонок из DataFrame
    columns_def = []
    for col in df.columns:
        # Получение типа данных колонки в виде строки
        col_type = str(df[col].dtype)
        # Нахождение соотвествия этому типу - типа БД
        pg_type = dtype_mapping.get(col_type, 'TEXT')
        # Добавление в список колонок новой колонки (название + тип)
        columns_def.append(f'"{col}" {pg_type}')
    # Создание таблицы
    create_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_def)})"
    try:
        database.post(create_query)
        print(f"Таблица {table_name} создана с колонками:")
        logger.info(f"Таблица {table_name} создана с колонками:")
        for col in df.columns:
            print(f"  - {col}")
            logger.info(f"  - {col}")
    except Exception as e:
        logger.error(f"Ошибка при создании таблицы: {e}")
        raise

# Подключение к БД
logger.info("Подключение к базе данных")
database = PGDatabase(
    host=DATABASE_CREDS['HOST'],
    database=DATABASE_CREDS['DATABASE'],
    user=DATABASE_CREDS['USER'],
    password=DATABASE_CREDS['PASSWORD'],
)
logger.info("Подключение к БД установлено")

# Сбор первоначальных данных
print("Сбор данных")
logger.info("Начало сбора данных из API")
# Вызов функции для единоразового накопления истории
oldest, df = find_old_date()
if oldest:
    print(f"Самая старая дата с данными: {oldest.strftime('%Y-%m-%d')}")
    logger.info(f"Самая старая дата с данными: {oldest.strftime('%Y-%m-%d')}")
# Создание таблицы и загрузка данных
if not df.empty:
    logger.info(f"Получено {len(df)} строк данных. Начинаем загрузку в БД...")
    # Вызов функции создания таблицы sales в БД
    create_table(database, df, 'sales')
    # Вызов функции загрузки данных из датафрейма в БД
    load_dataframe_to_db(df, database, 'sales')
    logger.info("ETL процесс завершен успешно")
else:
    print("Нет данных для загрузки")
    logger.warning("Нет данных для загрузки")
