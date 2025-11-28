import os
import sys
import time
import json
import shutil
import requests
import subprocess
from pathlib import Path
from zipfile import ZipFile


CONFIG_PATH = Path("resources/config.json")


with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    cfg = json.load(f)

version = cfg.get("version")
repository_url = cfg.get("repository_url")

print("Проверка наличия обновлений...")

try:
    response = requests.get(repository_url)
    response.raise_for_status()
    data = response.json()
    latest_version = data.get("tag_name", "NotFound")
except Exception as e:
    print("Не удалось получить данные с GitHub:", e)
    latest_version = "NotFound"

if latest_version == "NotFound":
    print("Репозиторий не найден на GitHub... Продолжаю...")

elif version != latest_version:
    choice = input(f"Найдена более новая версия {version} -> {latest_version}. \nХотите установить? (Y/N) ").strip().lower()
    if choice != "y":
        print("Вы отказались от установки обновления. Пропускаю...")
    else:
        print("Вы выбрали установить обновление. Запускаю процесс обновления...")

        temp_dir = Path(os.getenv("TEMP")) / f"update_{int(time.time())}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Получаем ссылку на zip
        assets = data.get("assets", [])
        if not assets:
            print("Нет файлов для скачивания")
            sys.exit(1)

        download_url = assets[0].get("browser_download_url")
        if not download_url:
            print("Ссылка на скачивание не найдена")
            sys.exit(1)

        zip_path = temp_dir / "update.zip"
        print("Скачивание обновления...")
        r = requests.get(download_url, stream=True)
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(r.raw, f)

        print("Распаковка обновления...")
        with ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        print("Обновление файлов программы...")
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.name == "config.json" and "resources" in str(file_path.parent):
                    continue
                shutil.copy(file_path, Path(".") / file_path.name)

        shutil.rmtree(temp_dir)
        print("Обновление завершено!")
else:
    print("Установленная версия соответствует актуальной версии...")


subprocess.run([sys.executable, "main.py"])
