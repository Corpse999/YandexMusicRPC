import os
import time
import msvcrt
import getpass
import subprocess
import win32com.client
from modules.discord_rpc import DiscordRPC
from modules.flask import YandexMusicFlaskApp
from modules.websocket import GetWebSocketURL
from modules.config import LoadConfig, ChangeConfig

class Console:
    def __init__(self):
        self.cfg = LoadConfig()
        self.cfg_changer = ChangeConfig()
        self.username = getpass.getuser()
        self.yandex_music_path = None
        self.ym_exe_path = None
    
    def check_ym_path(self, path=None):
        while True:
            if path is None:
                # Проверка, сохранен ли уже у Вас путь в конфиге
                if (users_path:=self.cfg.user_yandex_music_path) is not None:

                    # Если путь действителен, то возвращаемся
                    if os.path.exists(users_path):
                        self.yandex_music_path = self.cfg.user_yandex_music_path 
                        print("Ранее сохранненый путь найден!")
                        return
                    
                    # Если же путь недействителен, то сбрасываем его в конфиге
                    self.cfg_changer.change_json(key="user_yandex_music_path", value=None)
                    path = input("Путь, указанный в конфиге, устарел! Пожалуйста, укажите новый: ").strip()
                    continue
                    
                # Если первая проверка фейл, то смотрим дефолтный путь ЯМ
                default_path = self.cfg.default_yandex_music_path.format(username=self.username)
                if os.path.exists(default_path):
                    self.cfg_changer.change_json(key="user_yandex_music_path", value=default_path)
                    self.yandex_music_path = default_path
                    print("В конфиг был внесен стандартный путь к ярлыку Яндекс Музыки!")
                    return
                else:
                    path = input("Не удалось найти ярлык Яндекс Музыки по стандартному пути. Пожалуйста, укажите новый: ")
                    continue

            else:
                if os.path.exists(path):
                    self.cfg_changer.change_json(key="user_yandex_music_path", value=path)
                    self.yandex_music_path = path
                    print(f"Путь {path} успешно внесен в конфиг!")
                    return
                print(f"Ярлык не найден. Путь: {path}")
                path = input("Пожалуйста, введите корректный путь к ярлыку Яндекс Музыки: ").strip()
        
    def change_ym_arguments(self, shortcut):
        shortcut.Arguments = self.cfg.yandex_music_arguments.format(port=self.cfg.yandex_music_port)
        shortcut.Save()
        print("Параметры запуска успешно изменены!")
        return

    def check_ym_arguments(self):
        ym_path = self.yandex_music_path
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(ym_path)
        current_arguments = shortcut.Arguments
        self.ym_exe_path = shortcut.Targetpath
        if current_arguments != self.cfg.yandex_music_arguments.format(port=self.cfg.yandex_music_port):
            print("Неверные параметры запуска! Изменяю...")
            self.change_ym_arguments(shortcut)
        else:
            print("Параметры запуска корректны!")
        return
    
    def restart_yandex_music(self):
        # Килл процесса, если он есть
        exe_name = os.path.basename(self.ym_exe_path)
        subprocess.run(
            ["taskkill", "/IM", exe_name, "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        time.sleep(1)

        DETACHED_PROCESS = 0x00000008 # флаг для запуска без консоли
        CREATE_NEW_PROCESS_GROUP = 0x00000200 # флаг для создания новой группы процессов

        args = self.cfg.yandex_music_arguments.format(port=self.cfg.yandex_music_port)

        # Открытие ЯМ
        subprocess.Popen(
            [
                self.ym_exe_path,
                *args.split()
            ],
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,

            # Отключение вывода в консоль
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )

    def get_websocket_url(self):
        websocket_dict = GetWebSocketURL().ws
        if websocket_dict.get("success", False):
            return websocket_dict.get("ws")
        return None

    def find_websocket(self):
        timeout = 20
        interval = 1 

        for attempt in range(2):
            # На второй попытке даем 30 секунд и каждую секунду ищем ссылку на вебсокет ЯМ
            if attempt == 1:
                while timeout - interval > 0:
                    timeout-=interval
                    if (ws_url:=self.get_websocket_url()) is not None:
                        print("Ссылка на вебсокет найдена!")
                        return ws_url
                    time.sleep(1)

            if (ws_url:=self.get_websocket_url()) is not None:
                print("Ссылка на вебсокет найдена!")
                return ws_url
            
            else:
                if attempt == 0:
                    # Первая попытка неудачна = перезагрузка
                    print("Ссылка на вебсокет не найдена. Перезагружаю Яндекс Музыку...")
                    self.restart_yandex_music()
                    continue
                    
                else:
                    # Вторая попытка неудачна = ошибка
                    print("Не удалось получить ссылку на вебсокет после перезагрузки.\n\n" \
                          "Пожалуйста, напишите мне о возникшей проблеме на почту: corpse@corpse.pw")
                    return None

    def run(self):
        print("Поиск ярлыка Яндекс Музыки..."); self.check_ym_path()
        print("Проверка параметров запуска..."); self.check_ym_arguments()
        print("Поиск активного вебсокета")
        if (websocket_url:=self.find_websocket()) is None: return
        # Чистим консоль от мусора
        os.system("cls")
        print(f"Здравствуйте, {self.username}!\n")
        print("Выберите, что Вы хотите запустить:")
        print("   1. Эмбед Яндекс Музыки для OBS")
        print("   2. RPC Яндекс Музыки для Discord")
        print("   3. Почта для связи с создателем")
        print("   0. Выход")
    
        while True:
            print("\nНажмите клавишу выбора: ", end="", flush=True)
            key = msvcrt.getch()
            print(key.decode('cp1251', errors='ignore'), flush=True)
            
            if key == b'1':
                print("\nЗапускаю локальную страницу для OBS...")
                os.system("cls")
                YandexMusicFlaskApp(flask_port=self.cfg.flask_port).run_loop(websocket_url)
                break
            elif key == b'2':
                print("Запускаю Discord RPC...")
                os.system("cls")
                DiscordRPC().run_loop(websocket_url)
                break
            elif key == b'3':
                print("\nВ случае, если у вас возникли какие-то вопросы, не стесняйтесь писать мне на почту: corpse@corpse.pw")
                break
            elif key == b'0':
                print("\nВыход из программы...")
                break
            else:
                print("\nНеверный выбор! Попробуйте снова.")


console = Console()
console.run()