import os 
import subprocess
from modules.config import LoadConfig


class GetWebSocketURL:
    def __init__(self):
        self.js_script_path = os.path.join(os.getcwd(), "static", "get_ws.js")
        self.cfg = LoadConfig()

    def get_ws_url_from_node(self):
        try:
            result = subprocess.run(
                ["node", self.js_script_path, str(self.cfg.yandex_music_port), self.cfg.target_app],
                capture_output=True,
                text=True,
                timeout=5
            )
            ws_url = result.stdout.strip()
            if not ws_url:
                return {"success": False, "error": "Не удалось получить ссылку на вебсокет"}
            return {"success": True, "ws": ws_url}
        except Exception as e:
            return {"success": False, "error": e}

    @property
    def ws(self) -> dict :
        """
        Отдает:
        1) {"success": False, "error": <Error>}
        2) {"success": True, "ws": <Websocket URL>}
        """
        ws_url_dict_str = self.get_ws_url_from_node()
        return ws_url_dict_str
