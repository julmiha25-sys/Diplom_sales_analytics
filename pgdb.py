# Импорт библиотеки для подключения к PostgreSQL из Python
import psycopg2
# Класс для подключения к БД

class PGDatabase:
    # Функция для подключения к БД
    def __init__(self, host, database, user, password):
        # Сохранение параметров подключения как атрибутов объекта
        self.host=host 
        self.database=database 
        self.user=user
        self.password=password

        # Установка соединения с БД
        self.connection=psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
         )

        # Создание курсора для выполнения SQL-запросов
        self.cursor=self.connection.cursor()
        # Включение автоматического коммита изменений
        self.connection.autocommit=True

    # Функция для выполнения SQL-запросов с параметрам, которые передаются отдельно (защита от SQL-инъекций) 
    def post(self, query, args=()):
        try:
            self.cursor.execute(query, args)
        except Exception as err:
            print(repr(err))
    
    # Функция массовой вставки данных
    def post_many(self, query, args_list):
        try:
            self.cursor.executemany(query, args_list)
        except Exception as err:
            print(repr(err))



