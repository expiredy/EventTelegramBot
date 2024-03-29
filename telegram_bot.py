"""TODO: write total scenerio for all interactions with client.
   TODO: move all bot's lines into a separate file for more flexable interactions and editing"""
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

USERNAME_STARTING_SYMBOL = "@"



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
        self.__active_commands_array = {"/start": self.__register_user, #Starting command for new users, which will have behavior of "/help" command, if user is already logged in
                                        "/help": self.__send_help_message,  #Command for showcase of all available commands and mechanics of bot

                                        "/send": self.__fast_event_send, #Shortcut for sending events to groups and users
                                        "/add": self.__add_new_event, #Event planner
                                        "/ready":  self.__set_user_event_to_upload, #After everything about the event is set, it is a time to upload it into database

                                        "/edit": None,
                                        "/del": None,
                                        "/wait": None,
                                        "/resume": None, 

                                        "/create_group": None,


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
        try:
            response = get_api_response()
            debug_log(response)
            self.enter_debug_mode()
        except:
            self.stop_server()

    def run(self):
        debug_log("Server has been started")
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
                await self.__active_commands_array[command_entity["text"]](command_entity)
                return
            elif self.__running_sessions_pool[command_entity["from"]["id"]].users_recording_flag and command_entity["entities"][0]["type"] == "mention":
                for user_tag in command_entity["text"].replace(" ", "").split(USERNAME_STARTING_SYMBOL):
                    if user_tag == "":
                        continue
                    try:
                        self.__running_sessions_pool[command_entity["from"]["id"]].invited_users.add(self.__add_user_to_event(user_tag))
                    except Exception:
                        logging.exception("message")
                        await self.__send_message(command_entity["from"]["id"], "Простите, но не удалось найти человека с ником @" + user_tag )
                return
            raise Exception

        async def process_event_content(message_data: dict) -> None:
            if self.__running_sessions_pool[message_data["from"]["id"]].message_text is str:   
               self.__running_sessions_pool[message_data["from"]["id"]].set_invite_text(message_data[MESSAGE_TEXT_KEY]) 
               await self.__send_message(message_data["from"]["id"], "Отправьте название группы, к которой вы хотите подвязать это событие или введите ники пользователей!\nКогда всё будет готово введите команду /ready")
            elif self.__running_sessions_pool[message_data["from"]["id"]].users_recording_flag and\
                 ("entities" not in message_data or message_data["entities"][0]["type"] != "bot_command"):
                try: 
                    response = self.__database_session.get_users_from_group(message_data["text"])
                    self.__running_sessions_pool[message_data["from"]["id"]].invited_users.update(response)
                    debug_log(self.__running_sessions_pool[message_data["from"]["id"]].invited_users)
                except Exception:
                    await self.__send_message(message_data["from"]["id"], "Простите, но не удалось найти группу с названием " + message_data["text"])
                
        async def process_common_message(message_data: dict) -> None:
            #TODO: Add a check of allowing sending messages for current user             

            if any(joke_trigger in message_data[MESSAGE_TEXT_KEY].lower() for joke_trigger in ["анекдот", "шутка"]):
                if any(joke_trigger in message_data[MESSAGE_TEXT_KEY].lower() for joke_trigger in ["пожалуйста", "пж ", " пж", "пжшка", "пжлста", "пжлст"]):
                    await self.__send_message({message_data["from"]["id"]},
                                               requests.get('http://rzhunemogu.ru/RandJSON.aspx?CType=1').text[12:-2])
                else:
                    await self.__send_message({message_data["from"]["id"]}, "А можно повежливее?")
                return
            await self.__send_message({message_data["from"]["id"]}, "Немного не понял, простите, пожалуйста")


        async def callback_processor(message_data: dict) -> None:
            for callback_data in message_data["callback_query"]:
                pass

        update_log = get_api_response(request_method=requests.post,
                                      method_name="getUpdates",
                                      parameters_dict={"allowed_updates": UPDATING_EVENTS_LIST})
        if RESULT_DATA_KEY not in list(update_log.keys()) or not update_log[RESULT_DATA_KEY]:
            return
        try:
            # handling 
            for update_event in update_log[RESULT_DATA_KEY]:
                if update_event["update_id"] <= self.__last_handled_update_event_id:
                    continue
                if MESSAGE_DATA_KEY in list(update_event.keys()) and MESSAGE_TEXT_KEY in list(update_event[MESSAGE_DATA_KEY].keys()):
                    debug_log(update_event[MESSAGE_DATA_KEY]["text"], "\n /*sended from*/ ",
                            update_event[MESSAGE_DATA_KEY]["from"]["first_name"], " id :",
                            update_event[MESSAGE_DATA_KEY]["from"]["id"], "\n")
                    try:
                        await process_command_message(update_event[MESSAGE_DATA_KEY])
                    except:
                        if update_event[MESSAGE_DATA_KEY]["from"]["id"] in self.__running_sessions_pool:
                            await process_event_content(update_event[MESSAGE_DATA_KEY])
                        else:
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
    
    async def __send_message(self, sending_to_chat_ids_set: set, message: str, reply_markup_object: dict = {}, signature_username: str = None):
        def get_signatured_message(message):
            return "Сообщение было отправлено " + signature_username + "\n" + message 

        def form_inline_keyboard_markup():
            import json
            # reply_markup_object["keyboard"] = [[]]
            reply_markup_object["inline_keyboard"] = [[{'text': "Sheesh", 'callback_data': "AAA"}]]
            return json.dumps(reply_markup_object)
        
        
        if signature_username:
            debug_log("Ready to be sent")
            message = get_signatured_message(message)

        reply_markup_object = form_inline_keyboard_markup()
        print(reply_markup_object)
        request_data = {'chat_id': sending_to_chat_ids_set, 'text': message, 'reply_markup': reply_markup_object}
        response = get_api_response(requests.post, "sendMessage", request_data)
        debug_log("response ", response["ok"])
        if not response["ok"]:
            debug_log(response)

    '''
    User events
    '''
    async def __login_user(self):
        pass

    def __add_user_to_event(self, username: str) -> int:           
        try:
            debug_log(username)
            user_chat_id = self.__database_session.get_user_id_by_username(username)
            debug_log("chat id: ", user_chat_id)
            if  self.__database_session.check_for_user(user_chat_id):
                return user_chat_id
            else:
                raise Exception
        except requests.exceptions.RequestException:
            debug_log(f"error, getting id by username: {username}")
            pass


    '''
    Default commands handlers
    '''
    
    async def __register_user(self, new_user_message: dict):
        if not self.__database_session.check_for_user(new_user_message["from"]["id"]):
            self.__database_session.add_new_user(new_user_message["from"]["id"], new_user_message["from"]["username"], 0)
        else:
            await self.__send_help_message(new_user_message, preface="Вы уже зарегистрированы в системе, вот небольшая справака о доступных командах")

    
    async def __fast_event_send(self, command_data: dict):
        if command_data["from"]["id"] in self.__running_sessions_pool:
            await self.__send_message(command_data["from"]["id"], "Вы уже и так создаёте событие")
        self.__running_sessions_pool[command_data["from"]["id"]] = EventDataSession()
        await self.__send_message(command_data["from"]["id"], "Отправьте текст приглашания, которое вы хотите разослать")


    async def __add_new_event(self, message_data: dict):
        debug_log("event added")
        self.__running_sessions_pool[message_data["from"]["id"]] = EventDataSession()
        await self.__send_message({message_data["from"]["id"]}, "Отправьте сообщение, которое вы хотите отправить")


    async def __choose_date(self, user_id: int, callaback_action_index: int = 0):
        def genereate_calendar(month_skip_count):
            from datetime import timedelta
            current_date = get_current_time_point() +  timedelta(month=month_skip_count)

        await self.__send_message(user_id, "Choose a date of your event:", reply_markup_object=genereate_calendar())


    async def __set_user_event_to_upload(self, user_message):
        try:
            self.__running_sessions_pool[user_message["from"]["id"]].invited_users.remove(user_message["from"]["id"])
        except KeyError:
            pass

        for user_chat_id in self.__running_sessions_pool[user_message["from"]["id"]].invited_users:
            try:
                await self.__send_message(user_chat_id,
                                        self.__running_sessions_pool[user_message["from"]["id"]].message_text)
                debug_log(f'Message was sent to: {user_chat_id}')
            except:
                debug_log(f'Message was NOT sent to: {user_chat_id}')

        await self.__send_message(user_message["from"]["id"], "Всё отправлено)")
        self.__running_sessions_pool[user_message["from"]["id"]] = None


    async def __send_help_message(self, user_command, preface: str = ""):
        await self.__send_message(user_command["from"]["id"], preface + "\n" + self.__get_functionality_help_message())



    '''
    events processing methods
    ''' 
    async def __check_for_passed_events(self):
        current_time_point = get_current_time_point()
        for event_data_index in range(len(self.__events_pool)):
            if self.__events_pool[event_data_index]["time"] < current_time_point:
                pass

                del self.__events_pool[event_data_index]
        self.__events_pool_update()_check_for_passed_events

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

    
    '''
    Message generators
    '''
    def __get_functionality_help_message(self) -> str:
        return "Тебе никто не поможет\nНа самом деле это шутка, просто пока эта команда не работает"


    '''
    data saving things
    '''
    def __upload_session_progress(self, data_dict: dict):
        import pickle
        pickle.dump(data_dict, open(self.__configuration_file_path, "wb"))
        debug_log("Everything is saved")
    
    def __load_last_session_progress(self, variable_key: str):
        import pickle
        return pickle.load(open(self.__configuration_file_path, "rb"))[variable_key]


'''Responding configuration classes'''  

    
'''Data classes'''

class EventDataSession:
    message_text = str
    invited_users = set
    users_recording_flag = False

    def __init__(self):
        self.invited_users = set()

    def set_invite_text(self, message_text: str):
        self.message_text = message_text
        self.users_recording_flag = True

    def get_all_invited_users(self) -> set:
        return self.invited_users

    def set_timer(self, time_inaccuracies: str):
        pass


class MainPanelGenerator:
    def __init__(self):
        pass

    def __repr__(self):
        pass


def get_current_time_point():
    return datetime.now()


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