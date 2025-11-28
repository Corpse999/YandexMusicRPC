import logging
from modules.ym_functions import YandexMusicInfo
from flask import Flask, render_template, jsonify


class YandexMusicFlaskApp:
    def __init__(self, flask_port):
        self.app = Flask(__name__,
                         template_folder="../templates",
                         static_folder="../static"
                        )
        self.flask_port = flask_port
        self.ym_info_class = YandexMusicInfo()

        self._setup_routes()

    # Пути фласки
    def _setup_routes(self):
        @self.app.route("/")
        def index():
            return render_template("index.html")

        @self.app.route("/current_track")
        def current_track_api():
            return jsonify(self.ym_info_class.current_track)

    # Функция запуска фласки
    def run_flask(self):
        logging.getLogger('werkzeug').disabled = True
        print("Локальная страница успешно развернута!\n"\
              f"Ссылка: http://127.0.0.1:{self.flask_port}\n\n")
        self.app.run(debug=False, use_reloader=False, port=self.flask_port)

    # Функция старта главного лупа (и фласка, и получение инфы с ЯМ)
    def run_loop(self, ws_url):
        self.ym_info_class.start_ws_client(ws_url)
        self.run_flask()