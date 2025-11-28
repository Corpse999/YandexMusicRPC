import os
import json

CONFIG_PATH = os.path.join(os.getcwd(), "resources", "config.json")

class LoadConfig:
    def __init__(self):
        with open(CONFIG_PATH, "r", encoding="UTF-8") as cfg:
            self._config = json.load(cfg)

    def __getattr__(self, name):
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"{name} не найден в конфиге")
    
    @property
    def config(self):
        return self._config

    @property
    def all_attrs(self):
        return [k for k in self.config.keys()]
    
class ChangeConfig:
    def read_json(self):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_json(self, data):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            return
    
    def change_json(self, key, value):
        data = self.read_json()
        data[key] = value
        self.save_json(data)
        return