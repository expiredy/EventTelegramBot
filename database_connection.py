import sqlite3

class DatabaseClient:
    database_connection = sqlite3.connect
    database_cursor = None


    def __init__(self, database_path: str):
        self.database_connection = sqlite3.connect(database_path)
        self.database_cursor = self.database_connection.cursor()

    def add_new_user():
        pass

    def close_connection(self) -> None:
        self.database_connection.commit()
        self.database_connection.close()
        

if __name__ == "__main__":
    test_database = DatabaseClient("./users.db")
    # test_database.close_connection()