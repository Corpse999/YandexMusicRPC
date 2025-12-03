import time
import random
import discordrpc
from modules.config import LoadConfig
from discordrpc import Activity, StatusDisplay
from modules.ym_functions import YandexMusicInfo


class DiscordRPC:
    def __init__(self):
        self.ym_info_class = YandexMusicInfo()
        self.client_id = LoadConfig().discord_rpc_client_id
        self.rpc = discordrpc.RPC(self.client_id, output=False)
        self.default_ym_url = "https://music.yandex.ru/track/"
        self.time_started = None
        self.prev_track = None
        self.change_rpc = 0

        self.random_statuses = [
            "В поисках вдохновения...",
            "В наслаждении тишиной..."
        ]

        # По умолчанию ---------------------------
        self.default_thumbnail = "https://github.com/Corpse999/YandexMusicRPC/blob/test/resources/ym_wave.gif?raw=true"

        self.default_assets = {
            "small_text": "GitHub: Corpse999",
            "small_image": "https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png",
            "small_url": "https://github.com/Corpse999/YandexMusicRPC"
        }

        self.default_rpc = {
            "large_image": self.default_thumbnail,
            "details": random.choice(self.random_statuses),
        }
        # ----------------------------------------

    def parse_time(self, time):
        time_list = time.split(":")
        if len(time_list) > 3:
            raise Exception("Слишком большая строка времени. Максимум - часы:минуты:секунды")
        seconds = int(time_list[-1]) if len(time_list) >= 1 else 1
        minutes = int(time_list[-2]) if len(time_list) >= 2 else 0
        hours = int(time_list[-3]) if len(time_list) == 3 else 0
        return seconds + minutes*60 + hours * 3600
    
    def parse_track_url(self, track_url):
        try:
            url_parts = track_url.split("&")
            for part in url_parts:
                if "trackId" in part:
                    return self.default_ym_url + part.lstrip("trackId=")
            return None
        except:
            return None

    @property
    def custom_rpc(self):
        tot_time = self.time_started + self.parse_time(self.ym_info_class.current_track.get("time").get("total"))
        thumbnail = thumbnail_raw.replace("1000x1000", "400x400") if (thumbnail_raw:=self.ym_info_class.current_track.get("thumbnail")) is not None else self.default_thumbnail
        custom_rpc = {
            "details": self.ym_info_class.current_track.get("title"),
            "details_url": self.parse_track_url(self.ym_info_class.current_track.get("track_url")),
            "state": ", ".join(self.ym_info_class.current_track.get("authors")),
            "large_image": thumbnail,
            "ts_start": self.time_started,
            "ts_end": tot_time
        }  

        custom_rpc = {**custom_rpc, **self.default_assets}

        # Если на паузе, то добавляем картинку паузы
        if self.ym_info_class.current_track.get("status") == "paused":
            custom_rpc["small_image"] = "https://github.com/Corpse999/YandexMusicRPC/blob/main/static/paused.png?raw=true"
            custom_rpc["small_text"] = "На паузе"
            custom_rpc["small_url"], custom_rpc["ts_start"], custom_rpc["ts_end"] = None, None, None

        return custom_rpc


    def run_rpc(self):
        while True:
            # Делаем двойную проверку: если отсутствуют название и авторы, то ставим дефолтный RPC
            if ((track_title:=self.ym_info_class.current_track.get("title")) is None and not self.ym_info_class.current_track.get("authors")):
                self.rpc.set_activity(**self.default_rpc,
                                      **self.default_assets,
                                      status_type=StatusDisplay.Details,
                                      act_type=Activity.Listening)
            elif not self.ym_info_class.current_track.get("time").get("current"):
                continue
            else:
                parsed_time = self.parse_time(self.ym_info_class.current_track.get("time").get("current", 0))
                # Время из ЯМ (не из RPC)
                alternative_time_started = round(time.time() - parsed_time)
                # Задаем время начала трека
                if self.time_started is None: 
                    self.time_started = alternative_time_started
                
                # Текущее время, которое показывает RPC
                cur_time_discord = time.time() - (self.time_started or 0)

                # Если абсолютная разница текущего времени из ЯМ и текущего времени из RPC отличается на > 2, то вставляем время из ЯМ
                if abs(cur_time_discord - parsed_time) > 2:
                    self.time_started = alternative_time_started
                    self.change_rpc = 1

                # Делаем проверку, равен ли текущий тайтл прошлому. Если нет - меняем время и предыдущий тайтл, а так же обновляем RPC
                if self.prev_track != track_title: 
                    self.prev_track = track_title
                    self.time_started = alternative_time_started
                    self.change_rpc = 1

                if self.change_rpc == 1:
                    self.rpc.set_activity(**self.custom_rpc,
                                          status_type=StatusDisplay.Details,
                                          act_type=Activity.Listening,)
                    self.change_rpc = 0

            time.sleep(0.2)

    def run_loop(self, ws_url):
        print("Discord RPC был успешно запущен!")
        print(f"Подключено к: {self.rpc.User.name} ({self.rpc.User.id})")
        self.ym_info_class.start_ws_client(ws_url)
        self.run_rpc()
    