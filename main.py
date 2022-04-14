from telegram_bot import BotClient
from database_connection import DatabaseClient

def main():
    new_database_session = DatabaseClient(database_path="database/bot_data.db", active_debug_mode=True)
    bot_client = BotClient(new_database_session)
    bot_client.test_connection()
    bot_client.run()


if __name__ == "__main__":
    main()