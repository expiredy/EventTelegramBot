import requests
from os import getenv
from dotenv import load_dotenv
load_dotenv(".env")
import asyncio

from database_connection import DatabaseSession


API_URL = getenv('API_URL')
TELEGRAM_BOT_TOKEN = getenv('TELEGRAM_BOT_TOKEN')

class BotClient:
    active_users_profile = dict
    __session_active = bool
    __database_session = DatabaseSession
    __event_pool = list

    def __init__(self, database_session: DatabaseSession):
        self.__session_active = True
        self.__database_session = database_session
        self.__event_pool = []
        self.__set_default_commands()

    def test_connection(self):
        responce = requests.get(get_formed_request("getMe"))
        print(responce.text)
    
    def run(self):
        while self.__session_active:
            asyncio.run(self.__update())

    async def __update(self):
        update_log = requests.get(get_formed_request("getUpdates")).json()["result"]
        await self.__send_message({847751506}, "Fuck you")

    async def __send_message(self, sending_to_chat_ids_set: set, message: str):
        request_data = {'chat_id': sending_to_chat_ids_set, 'text': message}
        response = requests.post(get_formed_request("sendMessage"), request_data).json()
        print(response)

    '''events, for sending''' 
    async def __check_for_passed_events():
        pass

    async def __events_pool_update():
        pass

    '''
    hints for pings
    '''
    def __set_all_users_as_hints(self):
        pass
        
    def __set_users_groups_as_hints(self):
        pass

    async def __check_for_ended_timers(self):
        pass




def get_formed_request(method_name: str):
    return API_URL + TELEGRAM_BOT_TOKEN + "/" + method_name


def main():
    new_database_session = DatabaseSession()
    bot_client = BotClient(new_database_session)
    bot_client.test_connection()
    bot_client.run()


if __name__ == "__main__":
    main()
