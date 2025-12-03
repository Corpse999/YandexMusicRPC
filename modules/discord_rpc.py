import time
import random
from pypresence import Presence
from modules.config import LoadConfig
from pypresence import StatusDisplayType
from pypresence.types import ActivityType
from modules.ym_functions import YandexMusicInfo

class DiscordRPC:
    def __init__(self):
        self.ym_info_class = YandexMusicInfo()
        self.client_id = LoadConfig().discord_rpc_client_id
        self.rpc = Presence(client_id=self.client_id)
        self.time_started = None
        self.prev_track_title = None
        self.change_rpc = False
        self.cycles_to_change = 50 # каждые 10 секунд (50 * 0.02 сек) форсим обновление RPC (костыль для фикса фриза времени при быстром листании)

        self.random_statuses = [
            "В поисках вдохновения...",
            "В наслаждении тишиной..."
        ]

        # По умолчанию ---------------------------
        self.default_ym_url = "https://music.yandex.ru/track/"
        self.default_thumbnail = "https://github.com/Corpse999/YandexMusicRPC/blob/test/resources/ym_wave.gif?raw=true"

        self.default_assets = {
            "small_text": "GitHub: Corpse999",
            "small_image": "https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png",
            "small_url": "https://github.com/Corpse999/YandexMusicRPC",
            "activity_type": ActivityType.LISTENING,
            "status_display_type": StatusDisplayType.DETAILS, 
        }

        self.default_rpc = {
            "large_image": self.default_thumbnail,
            "details": random.choice(self.random_statuses),
        }
        # ----------------------------------------

    def parse_time(self, time):
        try:
            time_list = time.split(":")
            if len(time_list) > 3:
                raise Exception("Слишком большая строка времени. Максимум - часы:минуты:секунды")
            seconds = int(time_list[-1]) if len(time_list) >= 1 else 1
            minutes = int(time_list[-2]) if len(time_list) >= 2 else 0
            hours = int(time_list[-3]) if len(time_list) == 3 else 0
            return seconds + minutes*60 + hours * 3600
        except:
            return None
    
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
            "start": self.time_started,
            "end": tot_time
        }  

        custom_rpc = {**custom_rpc, **self.default_assets}

        # Если на паузе, то добавляем картинку паузы
        if self.ym_info_class.current_track.get("status") == "paused":
            custom_rpc["small_image"] = "https://github.com/Corpse999/YandexMusicRPC/blob/main/static/paused.png?raw=true"
            custom_rpc["small_text"] = "На паузе"
            custom_rpc["small_url"], custom_rpc["start"], custom_rpc["end"] = None, None, None

        return custom_rpc


    def run_rpc(self):
        self.rpc.connect()
        cycles_amount = 0
        while True:
            track = self.ym_info_class.current_track
            title = track.get("title")
            authors = track.get("authors")
            current_time = self.parse_time(track.get("time", {}).get("current"))

            # Ставим дефолтный RPC, если не удается получить авторов и название
            if (title is None and not authors) or current_time is None:
                self.rpc.update(**self.default_rpc,
                                **self.default_assets)
                self.prev_track_title = None
                self.time_started = None
                continue

            # Если трек поменялся, то скидываем время и ставим метку, что надо поменять RPC
            if title != self.prev_track_title:
                self.prev_track_title = title
                self.change_rpc = True
                cycles_amount = 0 # Сбрасываем счетчик при смене трека
                self.time_started = int(time.time() - current_time)

            # Сверяем текущее время в RPC и реальное время RPC. Если разница > 2 сек, то меняем время
            discord_time = time.time() - self.time_started
            if abs(discord_time - current_time) > 2:
                self.time_started = int(time.time() - current_time)
                self.change_rpc = True
            
            if cycles_amount == self.cycles_to_change:
                self.time_started = int(time.time() - current_time)
                cycles_amount = 0
                self.change_rpc = True

            if self.change_rpc:
                self.rpc.update(**self.custom_rpc)
                self.change_rpc = False
            
            # Прибавляем единичку к циклам для работы костыля
            cycles_amount += 1
            
            # Спим перед новым циклом
            time.sleep(0.2)


    def run_loop(self, ws_url):
        print("Discord RPC был успешно запущен!")
        self.ym_info_class.start_ws_client(ws_url)
        self.run_rpc()
    