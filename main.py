import requests
from os import getenv
from dotenv import load_dotenv
load_dotenv(".env")
import asyncio
from datetime import datetime

from database_connection import DatabaseClient

#Hints 
from collections.abc import Callable


API_URL = getenv('API_URL')
TELEGRAM_BOT_TOKEN = getenv('TELEGRAM_BOT_TOKEN')

UPDATING_EVENTS_LIST = ["message"]


class BotClient:
    active_users_profile = dict
    __session_active = bool
    __database_session = DatabaseClient
    __event_pool = list

    def __init__(self, database_session: DatabaseClient):
        self.__session_active = True
        self.__database_session = database_session
        self.__event_pool = []

        self.__events_pool_update()

    '''Test'''
    def test_connection(self):
        responce = get_api_response()
        print(responce.text)
    
    def run(self):
        while self.__session_active:
            asyncio.run(self.__update())

    def stop_server(self):
        self.__database_session.close_connection()
        self.__session_active = False

    async def __update(self):
        update_log = get_api_response(method_name="getUpdates",
                                      parametrs_dict={"allowed_updates": UPDATING_EVENTS_LIST}).json()
        # await self.__send_message({847751506}, "Fuck you")

    async def __send_message(self, sending_to_chat_ids_set: set, message: str):
        request_data = {'chat_id': sending_to_chat_ids_set, 'text': message}
        response = get_api_response(requests.post, "sendMessage", request_data).json()
        print(response)

    '''
    User events
    '''
    async def login_user(self):
        pass

    '''
    events, for sending
    ''' 
    async def __check_for_passed_events(self):
        current_time_point = datetime.now()
        for event_date in self.__event_pool:
            pass

    def __events_pool_update(self):
        pass

    async def __check_for_ended_timers(self):
        pass

    '''
    hints for pings
    '''
    def __set_all_users_as_hints(self):
        pass
        
    def __set_users_groups_as_hints(self):
        pass


def get_api_response(request_method: Callable = requests.get, method_name: str = "getMe", parametrs_dict: dict = {}):
    return request_method(API_URL + TELEGRAM_BOT_TOKEN + "/" + method_name, params=parametrs_dict)


def main():
    new_database_session = DatabaseClient(database_path="database/users.db")
    bot_client = BotClient(new_database_session)
    bot_client.test_connection()
    bot_client.run()


if __name__ == "__main__":
    main()