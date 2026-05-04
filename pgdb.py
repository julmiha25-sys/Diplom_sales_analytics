# Импорт библиотеки для подключения к PostgreSQL из Python
import psycopg2
import os

# Класс для подключения к БД
class PGDatabase:
    # Атрибут класса для хранения единственного экземпляра (Singleton)
    _instance = None
    
    # Контроль создания экземпляра (Singleton)
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    # Функция для подключения к БД
    def __init__(self, host=None, database=None, user=None, password=None):
        # Проверяем, был ли экземпляр уже инициализирован
        if not hasattr(self, '_initialized'):
            # Сохранение параметров подключения как атрибутов объекта
            self.host = host or os.getenv('DB_HOST', 'localhost')
            self.database = database or os.getenv('DB_NAME', 'postgres')
            self.user = user or os.getenv('DB_USER', 'postgres')
            self.password = password or os.getenv('DB_PASSWORD', '')

            # Установка соединения с БД
            self.connection = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
            )

            # Создание курсора для выполнения SQL-запросов
            self.cursor = self.connection.cursor()
            # Включение автоматического коммита изменений
            self.connection.autocommit = True
            
            # Отмечаем, что инициализация выполнена
            self._initialized = True
    
    # Метод для получения единственного экземпляра класса (Singleton)
    @classmethod
    def get_instance(cls):
        # Если экземпляр не создан, то он создается автоматически
        if cls._instance is None:
            # Параметры берутся из переменных окружения
            cls._instance = cls()  
        return cls._instance

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


# Экземпляр создается автоматически при импорте модуля
db = PGDatabase.get_instance()