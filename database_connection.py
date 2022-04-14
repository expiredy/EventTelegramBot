import sqlite3
from submodules import debug_log
from typing import Final

DATABASE_TABLE_NAME_KEY: Final = "NAME"
DATABASE_TABLE_PARAMETERS_STRUCTURE_KEY: Final = "PARAMETERS_STRUCTURE"

DATABASES_STRUCTURE_BLUEPRINTS = [
    {
    DATABASE_TABLE_NAME_KEY:
        "users", 
    DATABASE_TABLE_PARAMETERS_STRUCTURE_KEY: 
        '''
        (
            telegram_id    BIGINT  PRIMARY KEY
                                NOT NULL,
            username       STRING  NOT NULL,
            access_role_id INTEGER
                );
        '''
    },

    {
    DATABASE_TABLE_NAME_KEY:
        "users_roles",
    DATABASE_TABLE_PARAMETERS_STRUCTURE_KEY:
        '''
        (
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
        "events",
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
        "users_groups",
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
            
    def add_new_user(self, user_telegram_id: int):
        pass

    def close_connection(self) -> None:
        self.database_connection.commit()
        self.database_connection.close()

    def check_for_new_user(self, user_telegram_id: int):
        #Checking is there a dataframe in db with current user id
        pass

    def check_access_level(self, user_telegram_id: int, access_parameter: str) -> bool:
        self.database_cursor.execute("SELECT FROM users")

    def __check_need_for_initialization(self) -> bool:
        return not any(self.database_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall())
        
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
    debug_log(test_database)
    test_database.close_connection()