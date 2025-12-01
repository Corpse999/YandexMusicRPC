import os
import sys
import shutil
import zipfile
import tempfile
import requests
import keyboard
import subprocess
from packaging import version
from modules.config import LoadConfig, ChangeConfig


class Version:
    def __init__(self):
        self.current_config = LoadConfig()
        self.cfg_changer = ChangeConfig()
        self.config_path = os.path.join(os.getcwd(), "resources", "config.json")
        self.releases_url = self.current_config.repository_url
        self.users_settings = {key:self.current_config.config[key] for key in self.current_config.config if key in ["yandex_music_port",
                                                                                                                    "flask_port",
                                                                                                                    "user_yandex_music_path"]}

        self.current_version = version.parse(self.current_config.version.rstrip("v"))
        self.newer_version = None
        self.newer_version_url = None

    def get_newer_version(self):
        response = requests.get(self.releases_url).json()
        # Если нет релизов, то возвращаем None
        if "status" in response and response.get("status") == "404":
            return None

        self.newer_version = version.parse(response.get("tag_name").rstrip("v"))
        self.newer_version_url = response.get("zipball_url")

        return response

    @property
    def is_latest(self):
        return self.newer_version <= self.current_version
    
    def download_from_github(self):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
                r = requests.get(self.newer_version_url, stream=True)
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                
                temp_zip_path = tmp_file.name

            extract_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            subfolders = os.listdir(extract_dir)
            if len(subfolders) == 1:
                real_folder = os.path.join(extract_dir, subfolders[0])
            else:
                real_folder = extract_dir

            os.remove(temp_zip_path)

            print("Архив успешно загружен!")
            return real_folder
        except:
            return None
        
    def change_old_files(self, folder_path):
        print("Обновляю устаревшие файлы...")
        current_dir = os.getcwd()

        for root, _, files in os.walk(folder_path):
            try:
                for file in files:

                    source_file = os.path.join(root, file)

                    relative_path = os.path.relpath(root, folder_path)
                    target_dir = os.path.join(current_dir, relative_path)
                    target_file = os.path.join(target_dir, file)

                    os.makedirs(target_dir, exist_ok=True)

                    shutil.copy2(source_file, target_file)

                    if file.split(r"\"")[-1] == "config.json":
                        for k in self.users_settings:
                            self.cfg_changer.change_json(key=k, value=self.users_settings.get(k))
            except:
                pass

        print("Все файлы успешно обновлены!")
        return
        
    def start_updating(self):
        print("Загрузка архива с GitHub...")
        downloaded_path = self.download_from_github()
        if downloaded_path is None: print("Не удалось загрузить обновление"); return None
        self.change_old_files(downloaded_path)
    
    def run(self):
        print("Проверка наличия обновлений...")
        self.get_newer_version() # Обновляем переменные новой версии и ссылки на новую версию
        if self.newer_version is None:
            print("Репозиторий не найден на GitHub. Продолжаю...")

        elif self.is_latest is False:
            print(f"Найдена более новая версия {self.current_version} -> {self.newer_version}. \nУстановить? (Y/N)", end="", flush=True)
            while True:
                if keyboard.is_pressed('y'):
                    print(f"\nВы выбрали установить обновление. Обновляю до версии {self.newer_version}")
                    self.start_updating()
                    break

                elif keyboard.is_pressed('n'):
                    print("\nВы отказались от установки обновления. Продолжаю...")
                    break
        else:
            print("У вас установлена последняя версия. Продолжаю...")
        
        os.system("cls")
        
        subprocess.run([sys.executable, "main.py"])


ver = Version()
ver.run()

