import json
import textwrap
from typing import Iterable, Optional

import certifi
import pymongo
import pymysql
import pytds

from utility import logger, log_class


@log_class
class BaseDatabaseConnection:

    def __init__(self, user, pwd, host, port, database):
        self.user = user
        self.pwd = pwd
        self.host = host
        self.port = int(port)
        self.database = database
        self._cursor = self._connect_database()

    def _connect_database(self):
        raise NotImplementedError("Do not use 'BaseDatabaseConnection' object directly.")

    def execute_modify_sql(self, sql: str, args: dict = None):
        try:
            res = self._cursor.execute(sql, args)
            self._debug_print(sql=sql, res=res, args=args)
            self._connection.commit()
            return res
        except Exception as e:
            logger.error(f"Modify Error: {e}")
            self._connection.rollback()
            return None

    def execute_select_sql(self, sql: str, args: dict = None, fetchall: bool = False):
        try:
            self._cursor.execute(sql, args)
            if fetchall:
                res = self._cursor.fetchall()
            else:
                res = self._cursor.fetchone()
            self._debug_print(sql=sql, res=res, args=args)
            self._connection.commit()
            return res
        except Exception as e:
            logger.error(f"Query Error: {e}")
            return None

    def __del__(self):
        if hasattr(self, '_connection') and self._connection:
            self._connection.close()

    def _debug_print(self, sql: str, res: str, args: dict = None):
        logger.info(textwrap.dedent(
            """
            --------------------------------
            🐞 debug prints
            --------------------------------
            {formatted_sql}
            {formatted_args}
            {formatted_result}
            --------------------------------
            """
        ).format(
            formatted_sql=" ".join(sql.split()),
            formatted_args=json.dumps(args, default=str, ensure_ascii=False) if args else "No arguments provided",
            formatted_result=json.dumps(res, default=str, ensure_ascii=False)
        ))


class MsSqlDatabase(BaseDatabaseConnection):
    def _connect_database(self):
        try:
            self._connection = pytds.connect(dsn=self.host,
                                             port=self.port,
                                             user=self.user,
                                             password=self.pwd,
                                             database=self.database,
                                             as_dict=True)
            # print(f"Connect to MsSql Database: {self.host}")
            return self._connection.cursor()
        except Exception as e:
            logger.error(f"MsSQL Connect Fail: {e}")
            return None


class MySqlDatabase(BaseDatabaseConnection):
    def _connect_database(self):
        try:
            self._connection = pymysql.connect(host=self.host,
                                               port=self.port,
                                               user=self.user,
                                               password=self.pwd,
                                               database=self.database,
                                               cursorclass=pymysql.cursors.DictCursor)
            # print(f"Connect to MySql Database: {self.host}")
            return self._connection.cursor()
        except Exception as e:
            logger.error(f"MySQL Connect Fail: {e}")
            return None


class PyMongodb:
    def __init__(self, user, pwd, host, port, database):
        self.user = user
        self.pwd = pwd
        self.host = host
        self.port = int(port)
        self.database = database
        self._connection = None

    def _connect_database(self):
        try:
            connection_str = f"mongodb+srv://{self.user}:{self.pwd}@{self.host}/{self.database}?retryWrites=true&w=majority"
            self._connection = pymongo.MongoClient(connection_str, tlsCAFile=certifi.where())
            return self._connection[self.database]
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return None


class Database:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config):
        # Avoid redo initialized
        if hasattr(self, 'initialized'):
            return
        self.initialized = True

        self.config = config
        self.__connection = None

    @property
    def _connection(self):
        if self.__connection is None:
            user = self.config.user
            pwd = self.config.password
            host = self.config.host
            port = self.config.port
            database = self.config.database
            db_class = {
                'mssql': MsSqlDatabase,
                'mysql': MySqlDatabase
            }.get(self.config.driver.lower())

            self.__connection = db_class(user, pwd, host, port, database)
        return self.__connection

    def remove_dict_empty_value(self, dict_obj: dict):
        return {k: v for k, v in dict_obj.items() if v is not None and v != ""}

    def select(
            self, table: str, fields: Optional[Iterable[str]] = None,
            condition: Optional[Iterable[str]] = None,
            order_by: str = None, desc: bool = False):

        if not fields or not list(fields):
            fields_str = "*"
        else:
            fields_str = ', '.join(fields)

        sql = f"SELECT {fields_str} FROM {table} "

        if condition:
            condition_str = ' AND '.join(f"{field} = %({field})s" for field in condition)
            sql += f"WHERE {condition_str} "

        if order_by:
            order_type = "DESC" if desc else "ASC"
            sql += f"ORDER BY {order_by} {order_type}"

        return sql

    def update(self, table: str, fields: Iterable[str], condition: Optional[Iterable[str]] = None):

        fields_str = ', '.join(f"{field} = %({field})s" for field in fields)
        sql = f"UPDATE {table} SET {fields_str} "

        if condition:
            condition_str = ' AND '.join(f"{field} = %({field})s" for field in condition)
            sql += f"WHERE {condition_str} "

        return sql

    def delete(self, table: str, condition: Iterable[str]):
        conditions = ' AND '.join(f"{field} = %({field})s" for field in condition)
        sql = f"DELETE FROM {table} WHERE {conditions}"
        return sql

    def create(self, table: str, **fields) -> str:
        columns = ', '.join(fields.keys())
        values = ', '.join(
            f"'{v}'" if isinstance(v, str) else str(v) for v in fields.values()
        )
        sql = f"INSERT INTO {table} ({columns}) VALUES ({values});"
        return sql

    def execute_modify_sql(self, sql: str, args: dict = None):
        return self._connection.execute_modify_sql(sql, args)

    def execute_select_sql(self, sql: str, args: dict = None, fetchall: bool = False):
        return self._connection.execute_select_sql(sql, args, fetchall)


class MongoDB:
    def __init__(self, config):
        self.config = config
        self.__connection = None

    @property
    def _connection(self):
        if self.__connection is None:
            user = self.config.user
            pwd = self.config.password
            host = self.config.host
            port = self.config.port
            database = self.config.database

            # Initialize connection
            db = PyMongodb(user, pwd, host, port, database)
            self.__connection = db._connect_database()

        return self.__connection
