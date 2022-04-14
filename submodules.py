from threading import Thread

class EntityController(Thread):
    active_session = bool
    def __init__(self):
        self.active_session = True

    def run(self):
        while self.active_session:
            command_text = input()
            

def debug_log(*parameters) -> None:
    print(*parameters)



if __name__ == "__main__":
    test_thread = EntityController()
    test_thread.start()