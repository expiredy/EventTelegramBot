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


#Bot configuration variables
LAST_HANDLED_UPDATE_ID_KEY = "LAST_HANDLED_UPDATE_ID"

MAX_CHECKING_EVENTS = 10


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
    
    __events_pool = list
    __running_sessions_pool = dict
    __active_commands_array = dict

    __debug_mode = False
    __last_handled_update_event_id = int

    __configuration_file_path = str

    def __init__(self, database_session: DatabaseClient, configuration_file_path: str = DEFAULT_CONFIGURATION_FILE_PATH):
        self.__session_active = True
        self.__database_session = database_session

        self.__events_pool = []
        self.__running_sessions_pool = {}
        self.__active_commands_array = {"/start": None,
                                        "/send": None,
                                        "/add": self.__add_new_event,
                                        "/edit": None,
                                        "/del": None,
                                        "/wait": None,
                                        "/resume": None, 
                                        "/create_pool": None}

        self.__configuration_file_path = configuration_file_path
        try:
            self.__last_handled_update_event_id = self.__load_last_session_progress(LAST_HANDLED_UPDATE_ID_KEY)
        except EOFError:
            self.__last_handled_update_event_id = 0

        self.__events_pool_update()

        
    def enter_debug_mode(self):
        self.__debug_mode = True

    '''Test'''
    def test_connection(self):
        responce = get_api_response()
        debug_log(responce)
        self.enter_debug_mode()

    
    def run(self):
        while self.__session_active:
            try:
                asyncio.run(self.__update())
                asyncio.run(self.__check_for_passed_events())
            except KeyboardInterrupt:
                self.stop_server()

    def stop_server(self):
        if not self.__debug_mode:
            self.__database_session.close_connection()
        self.__upload_session_progress({LAST_HANDLED_UPDATE_ID_KEY: self.__last_handled_update_event_id})
        self.__session_active = False

    '''Method, which is calling every tick of main life cycle for executing real time events checking and responding'''
    async def __update(self):
        async def process_command_message(command_entity: dict) -> None:
            if len(command_entity["entities"]) == 1 and command_entity["entities"][0]["type"] == "bot_command":
                if command_entity["from"]["id"] not in list(self.__running_sessions_pool.keys()):
                    await self.__active_commands_array[command_entity["text"]](command_entity)
                    return

            raise Exception

        async def process_common_message(message_data: dict) -> None:
            #TODO: Add a check of allowing sending messages for current user  
            if message_data["from"]["id"] in list(self.__running_sessions_pool.keys()):
                if not self.__running_sessions_pool[message_data["from"]["id"]].message_text:
                    self.__running_sessions_pool[message_data["from"]["id"]].message_text = message_data["text"]
                # elif not self.__running_sessions_pool[message_data["from"]]["id"].add_user(message_data["text"]):
                #     await self.__send_message(message_data["from"]["id"], f'Неудалось найти аккаунт с ником "{message_data["text"]}"')
            

            elif any(joke_trigger in message_data[MESSAGE_TEXT_KEY].lower() for joke_trigger in ["анекдот", "шутка"]):
                if any(joke_trigger in message_data[MESSAGE_TEXT_KEY].lower() for joke_trigger in ["пожалуйста", "пж ", " пж", "пжшка", "пжлста", "пжлст"]):
                    await self.__send_message({message_data["from"]["id"]},
                                               requests.get('http://rzhunemogu.ru/RandJSON.aspx?CType=1').text[12:-2])
                else:
                    await self.__send_message({message_data["from"]["id"]}, "А можно повежливее?")
                return
            await self.__send_message({message_data["from"]["id"]}, "Sorry, don't get it, is this a joke?")

        update_log = get_api_response(request_method=requests.post,
                                      method_name="getUpdates",
                                      parameters_dict={"allowed_updates": UPDATING_EVENTS_LIST})
        if RESULT_DATA_KEY not in list(update_log.keys()) or not update_log[RESULT_DATA_KEY]:
            return
        try:
            for update_event in update_log[RESULT_DATA_KEY]:
                if update_event["update_id"] <= self.__last_handled_update_event_id or\
                     not MESSAGE_TEXT_KEY in list(update_event[MESSAGE_DATA_KEY].keys()):
                    continue
                debug_log(update_event[MESSAGE_DATA_KEY]["text"], "\n /*sended from*/ ",
                          update_event[MESSAGE_DATA_KEY]["from"]["first_name"], " ",
                          update_event[MESSAGE_DATA_KEY]["from"]["last_name"], " id :",
                          update_event[MESSAGE_DATA_KEY]["from"]["id"], "\n")
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
        debug_log("response ", response["ok"])

    '''
    User events
    '''

    async def register_user(self, new_user_id: int):
        self.__database_session.add_new_user(new_user_id)
        pass
    

    async def __login_user(self):
        pass

    async def add_user(self, username: str):
        if not username.startswith("@"):
            username =  "@" + username 
        try:
            chat_id = get_api_response(method_name="getChat", parameters_dict={"chat_id": username})
            if self.__database_session.check_for_user(chat_id):
                pass
        except requests.exceptions.RequestException:
            debug_log(f"error, getting id by username: {username}")
            pass


    '''
    Commands handlers
    '''
    async def __add_new_event(self, message_data):
        print("event added")
        self.__running_sessions_pool[message_data["from"]["id"]] = EventDataSession()
        await self.__send_message({message_data["from"]["id"]}, "Отправьте сообщение, которое вы хотите отправить")

    async def __edit_event(self):
        pass


    '''
    events, for sending
    ''' 
    async def __check_for_passed_events(self):
        current_time_point = datetime.now()
        for event_data_index in range(len(self.__events_pool)):
            if self.__events_pool[event_data_index]["time"] < current_time_point:
                pass

                del self.__events_pool[event_data_index]
        self.__events_pool_update()

    def __events_pool_update(self):
        for new_event_index in range(MAX_CHECKING_EVENTS - len(self.__events_pool)):
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


class EventDataSession:
    message_text = str
    invited_users = set
    current_creation_state = Callable

    def __init__(self):
        self.invited_users = set()
        self.current_registration_state = self.add_user

    def set_invite_text(self, message_text: str):
        self.message_text = message_text


    def set_timer(self, time_inaccuracies: str):
        pass



def message_preprocessor(processing_text: str) -> str:
    processing_text = " ".join(processing_text.split()).lower()
    return processing_text


def get_api_response(request_method: Callable = requests.get, method_name: str = "getMe", parameters_dict: dict = {}) -> dict:
    try:
        return request_method(str(API_URL + TELEGRAM_BOT_TOKEN + "/" + method_name), params=parameters_dict).json()
    except requests.exceptions.ConnectionError:
        debug_log("Error getting API response: \n")
        logging.exception("message")
        return {}
