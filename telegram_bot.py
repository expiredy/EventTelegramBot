from os import getenv
from dotenv import load_dotenv
load_dotenv(".env")

import requests
import asyncio
from datetime import datetime


from database_connection import DatabaseClient
from submodules import debug_log

#Hints 
from collections.abc import Callable
import logging

#secrets configuration
API_URL = getenv('API_URL')
TELEGRAM_BOT_TOKEN = getenv('TELEGRAM_BOT_TOKEN')
DEFAULT_CONFIGURATION_FILE_PATH = getenv('DEFAULT_CONFIGURATION_FILE_PATH')


#Bot configuration variables keys
LAST_HANDLED_UPDATE_ID_KEY = "LAST_HANDLED_UPDATE_ID"

# API configuration
UPDATING_EVENTS_LIST = ["message"]

#response keys configuration
RESULT_DATA_KEY = "result"
MESSAGE_DATA_KEY = "message"
MESSAGE_TEXT_KEY = "text"

#main bot client class
class BotClient:
    active_users_profile = dict
    __session_active = bool
    __database_session = DatabaseClient
    
    __event_pool = list
    __running_sessions_pool = list

    __debug_mode = False
    __last_handled_update_event_id = int

    __configuration_file_path = str

    def __init__(self, database_session: DatabaseClient, configuration_file_path: str = DEFAULT_CONFIGURATION_FILE_PATH):
        self.__session_active = True
        self.__database_session = database_session

        self.__event_pool = []
        self.__running_sessions_pool = []

        self.__configuration_file_path = configuration_file_path
        try:
            self.__last_handled_update_event_id = self.__load_last_session_progress(LAST_HANDLED_UPDATE_ID_KEY)
        except EOFError:
            self.__last_handled_update_event_id = 0

        self.__events_pool_update()

    '''Test'''
    def test_connection(self):
        responce = get_api_response()
        debug_log(responce)
        self.enter_debug_mode()
    
    def enter_debug_mode(self):
        self.__debug_mode = True
    
    def run(self):
        while self.__session_active:
            try:
                asyncio.run(self.__update())
            except KeyboardInterrupt:
                self.stop_server()

    def stop_server(self):
        if not self.__debug_mode:
            self.__database_session.close_connection()
        self.__upload_session_progress({LAST_HANDLED_UPDATE_ID_KEY: self.__last_handled_update_event_id})
        self.__session_active = False

    '''Method, which is calling every tick of main life cycle for executing real time events checking and responding'''
    async def __update(self):
        async def process_command_message(command_text: str) -> None:
            raise Exception

        async def process_common_message(message_data: str) -> None:
            if "анекдот" in message_data["text"].lower():
                await self.__send_message({message_data["from"]["id"]},
                                           requests.get('http://rzhunemogu.ru/RandJSON.aspx?CType=1').text[12:-2])

        update_log = get_api_response(request_method=requests.post,
                                      method_name="getUpdates",
                                      parameters_dict={"allowed_updates": UPDATING_EVENTS_LIST})
        if RESULT_DATA_KEY not in list(update_log.keys()) or not update_log[RESULT_DATA_KEY]:
            return
        try:
            # debug_log(update_log[RESULT_DATA_KEY])
            for update_event in update_log[RESULT_DATA_KEY]:
                if update_event["update_id"] <= self.__last_handled_update_event_id or\
                     not MESSAGE_TEXT_KEY in list(update_event[MESSAGE_DATA_KEY].keys()):
                    continue
                debug_log(update_event[MESSAGE_DATA_KEY]["text"], " /*sended from*/ ", update_event[MESSAGE_DATA_KEY]["from"]["id"])
                try:
                    await process_command_message(update_event[MESSAGE_DATA_KEY])
                except:
                    await process_common_message(update_event[MESSAGE_DATA_KEY])

            #Logging processed requests 
            self.__last_handled_update_event_id = update_event["update_id"]



        except IndexError:
            debug_log("Response corrupted: \n", update_log)
            if self.__debug_mode:
                self.stop_server()

        except KeyError:
            self.__last_handled_update_event_id = update_event["update_id"]
            debug_log(update_event)
            logging.exception("message")
    
    async def __send_message(self, sending_to_chat_ids_set: set, message: str):
        request_data = {'chat_id': sending_to_chat_ids_set, 'text': message}
        response = get_api_response(requests.post, "sendMessage", request_data)
        # debug_log(response["ok"])

    '''
    User events
    '''
    async def __login_user(self):
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

    # data saving things
    def __upload_session_progress(self, data_dict: dict):
        import pickle
        pickle.dump(data_dict, open(self.__configuration_file_path, "wb"))
    
    def __load_last_session_progress(self, variable_key: str):
        import pickle
        return pickle.load(open(self.__configuration_file_path, "rb"))[variable_key]




def message_preprocessor():
    pass


def get_api_response(request_method: Callable = requests.get, method_name: str = "getMe", parameters_dict: dict = {}):
    try:
        return request_method(str(API_URL + TELEGRAM_BOT_TOKEN + "/" + method_name), params=parameters_dict).json()
    except requests.exceptions.ConnectionError:
        debug_log("Error getting API response: \n")
        logging.exception("message")
        return {}
