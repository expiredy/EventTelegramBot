import sqlite3
from submodules import debug_log
from typing import Final

import logging

DATABASE_TABLE_NAME_KEY: Final = "NAME"
DATABASE_TABLE_PARAMETERS_STRUCTURE_KEY: Final = "PARAMETERS_STRUCTURE"

USERS_DATABASE_NAME: Final = "users"
USERS_ROLES_DATABASE_NAME: Final = "users_role"
EVENTS_DATABASE_NAME: Final = "events"
USERS_GROUPS_DATABASE_NAME: Final = "users_groups"

DATABASES_STRUCTURE_BLUEPRINTS = [
    {
    DATABASE_TABLE_NAME_KEY:
        USERS_DATABASE_NAME, 
    DATABASE_TABLE_PARAMETERS_STRUCTURE_KEY:
        '''
        (
            telegram_id    BIGINT  PRIMARY KEY
                                NOT NULL,
            access_role_id INTEGER,
            username       STRING  NOT NULL
        );
        '''
    },

    {
    DATABASE_TABLE_NAME_KEY:
        USERS_ROLES_DATABASE_NAME,
    DATABASE_TABLE_PARAMETERS_STRUCTURE_KEY:
        '''
        (.
            id                      PRIMARY KEY
                                        NOT NULL,
            getting_response        BOOLEAN DEFAULT (true) 
                                        NOT NULL,
            creating_global_groups  BOOLEAN NOT NULL
                                        DEFAULT (false) 
        )
        '''
    },

    {
    DATABASE_TABLE_NAME_KEY:
        EVENTS_DATABASE_NAME,
    DATABASE_TABLE_PARAMETERS_STRUCTURE_KEY:
        '''
        (
            id             INTEGER
                            NOT NULL,
            executing_time DATETIME
                            NOT NULL,
            content        STRING
                            NOT NULL,
            PRIMARY KEY (
                id
            )
        );
        '''
    }, 
    {DATABASE_TABLE_NAME_KEY:
        USERS_GROUPS_DATABASE_NAME,
    DATABASE_TABLE_PARAMETERS_STRUCTURE_KEY:
        '''
        (
            id      INTEGER PRIMARY KEY
                            NOT NULL,
            name    STRING  NOT NULL,
            members STRING
            );
        '''
    }
]


class DatabaseClient:
    database_connection = sqlite3.connect
    database_cursor = None
    database_name = str
    __debug_mode = False


    def __init__(self, database_path: str, active_debug_mode: bool = False):
        self.__debug_mode = active_debug_mode
        self.database_connection = sqlite3.connect(database_path)
        self.database_cursor = self.database_connection.cursor()
        self.database_name = self.__get_database_name(database_path)
        if self.__check_need_for_initialization():
            self.__initialize_empty_tables()
            
    def add_new_user(self, user_telegram_id: int, username: str, access_role_id: int):
        if not any(self.database_cursor.execute(f"""SELECT id FROM {USERS_ROLES_DATABASE_NAME} WHERE id = {access_role_id}""").fetchall()):
            debug_log("There is not role with id ", access_role_id)
            raise sqlite3.OperationalError
        try:
            self.database_cursor.execute(f"""
                                        INSERT INTO {USERS_DATABASE_NAME}   
                                            (telegram_id, access_role_id, username)
                                            VALUES
                                            ({user_telegram_id}, {access_role_id}, '{username}')
                                        """)
        except sqlite3.OperationalError:
            debug_log("Error with adding user in database")

        if self.__debug_mode:
            debug_log(f"user with id: {user_telegram_id} has been registered")
        self.update_database()
        
    def update_database(self):
        self.database_connection.commit()


    def close_connection(self) -> None:
        if not self.__debug_mode:
            self.update_database()
        self.database_connection.close()

    def check_for_user(self, user_chat_id: int):
        return any(self.database_cursor.execute(f"""SELECT telegram_id FROM {USERS_DATABASE_NAME} WHERE telegram_id = {user_chat_id}""").fetchall())

    def check_access_level(self, user_telegram_id: int, access_parameter: str) -> bool:
        try:
            current_user_access_role_id = self.database_cursor.execute(f"""SELECT telegram_id FROM {USERS_DATABASE_NAME} WHERE telegram_id = {user_telegram_id}""")
            self.database_cursor.execute(f"""SELECT {access_parameter}, id FROM {USERS_ROLES_DATABASE_NAME} WHERE id = {current_user_access_role_id}""")
        except sqlite3.OperationalError:
            return False

    def get_user_id_by_username(self, username: str) -> int:
        database_response = self.database_cursor.execute(f"""SELECT username, telegram_id FROM {USERS_DATABASE_NAME} WHERE username = '{username}'""").fetchall()
        debug_log("founded users: ", database_response)
        if len(database_response) != 1:
            raise sqlite3.OperationalError
        return database_response[0][1]

    def get_users_from_group(self, group_name: str) -> set: 
        users_set = None
        try: 
            database_response = self.database_cursor.execute(f"""SELECT name, members FROM {USERS_GROUPS_DATABASE_NAME} WHERE name = '{group_name}'""").fetchall()
            if len(database_response) != 1:
                raise sqlite3.OperationalError
            users_set = eval(database_response[0][-1])
        except: 
            debug_log("Error with getting group ", group_name)
        return users_set

    def __check_need_for_initialization(self) -> bool:
        return not any(self.database_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
        
    def __initialize_empty_tables(self):
        for db_structure in DATABASES_STRUCTURE_BLUEPRINTS:
            self.database_cursor.execute("CREATE TABLE " + db_structure[DATABASE_TABLE_NAME_KEY] + db_structure[DATABASE_TABLE_PARAMETERS_STRUCTURE_KEY])
            if self.__debug_mode:
                debug_log(f"Created database: {db_structure[DATABASE_TABLE_NAME_KEY]}")

    def __get_database_name(self, db_path: str):
        return db_path.split("/")[-1].replace(".db", "")

    def __str__(self):
        return self.database_name
        
        

if __name__ == "__main__":
    test_database = DatabaseClient("./database/bot_data.db", active_debug_mode=True)
    debug_log("connected to: ", test_database)
    print(test_database.check_for_user(847751506))
    print(test_database.get_user_id_by_username("NikitaTeletov"))
    test_database.close_connection()
