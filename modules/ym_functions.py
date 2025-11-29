import json
import time
import websocket
import threading

class YandexMusicWS:
    def __init__(self, parent, ws_url):
        self.parent = parent
        self.ws_url = ws_url
        self.ws = None
        self.running = True

    def send_eval(self, expression):
        self.parent.message_id += 1
        msg = {
            "id": self.parent.message_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "returnByValue": True
            }
        }
        self.ws.send(json.dumps(msg))

    def build_expression(self):
        return """
        (() => {
            const result = {
                title: null,
                authors: [],
                thumbnail: null,
                time: { current: null, total: null },
                status: null
            };
            const playerBar = [...document.querySelectorAll('*')].find(e =>
                e.classList && [...e.classList].some(cls => cls.includes('PlayerBar'))
            );
            if (!playerBar) return result;

            const metaTitleEl = [...playerBar.querySelectorAll('*')].find(e =>
                e.classList && [...e.classList].some(cls => cls.includes('Meta_title'))
            );
            if (metaTitleEl) result.title = metaTitleEl.textContent.trim();

            const separatedArtists = [...playerBar.querySelectorAll('*')].find(e =>
                e.classList && [...e.classList].some(cls => cls.includes('SeparatedArtists'))
            );
            if (separatedArtists) {
                const links = [...separatedArtists.querySelectorAll('*')].filter(e =>
                    e.classList && [...e.classList].some(cls => cls.includes('Meta_link'))
                );

                let authors = [];

                if (links.length > 0) {
                    authors = links.map(link => {
                        const caption = [...link.querySelectorAll('*')].find(e =>
                            e.classList && [...e.classList].some(cls => cls.includes('Meta_artistCaption'))
                        );
                        return caption ? caption.textContent.trim() : null;
                    }).filter(Boolean);
                } else {
                    const texts = [...separatedArtists.querySelectorAll('*')].filter(e =>
                        e.classList && [...e.classList].some(cls => cls.includes('Meta_text'))
                    );

                    authors = texts.map(t => t.textContent.trim()).filter(Boolean);
                }

                result.authors = authors;
            }

            const coverEl = [...playerBar.querySelectorAll('*')].find(e =>
                e.classList && [...e.classList].some(cls => cls.includes('PlayerBarDesktopWithBackgroundProgressBar_cover'))
            );
            if (coverEl) {
                const img = coverEl.querySelector('img');
                if (img && img.src) result.thumbnail = img.src;
            }

            const currentEl = [...playerBar.querySelectorAll('*')].find(e =>
                e.classList && [...e.classList].some(cls => cls.includes('TimecodeGroup_timecode_current_animation'))
            );
            if (currentEl) result.time.current = currentEl.textContent.trim();

            const totalEl = [...playerBar.querySelectorAll('*')].find(e =>
                e.classList && [...e.classList].some(cls => cls.includes('TimecodeGroup_timecode_end'))
            );
            if (totalEl) result.time.total = totalEl.textContent.trim();

            const playButton = [...playerBar.querySelectorAll('*')].find(e =>
                e.classList && [...e.classList].some(cls => cls.includes('BaseSonataControlsDesktop_playButtonIcon'))
            );
            if (playButton) {
                const useEl = playButton.querySelector('use');
                if (useEl && useEl.getAttribute('xlink:href') === '/icons/sprite.svg#play_filled_l') {
                    result.status = 'paused';
                } else if (useEl && useEl.getAttribute('xlink:href') === '/icons/sprite.svg#pause_filled_l') {
                    result.status = 'playing';
                }
            }

            return result;
        })()
        """

    def on_open(self, ws):
        threading.Thread(target=self.periodic_eval, daemon=True).start()

    def periodic_eval(self):
        while self.running:
            self.send_eval(self.build_expression())
            time.sleep(0.05)

    def on_message(self, ws, message):
        try:
            if isinstance(message, bytes):
                message = message.decode("utf-8", errors="ignore")
            data = json.loads(message)
            if "result" in data and "result" in data["result"]:
                value = data["result"]["result"].get("value")
                if value:
                    if value['thumbnail']:
                        value['thumbnail'] = value['thumbnail'].replace("100x100", "1000x1000")
                    updated_values = {key:value.get(key) for key in value if value.get(key) != self.parent.current_track.get(key)} # Обновляем в current_track только то, что изменилось
                    self.parent.current_track.update(updated_values)
        except:
            pass

    def on_error(self, ws, error):
        print("Ошибка:", error)

    def on_close(self, ws, code, msg):
        print("Закрыто:", code, msg)
        self.running = False

    def run(self):
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.run_forever(origin="null")

class YandexMusicInfo:
    def __init__(self):
        self.current_track = {
            "title": None,
            "authors": [],
            "thumbnail": None,
            "time": {"current": None, "total": None},
            "status": None
        }
        self.message_id = 0
        self.ws_client = None
        self.ws_url = None

    def start_ws_client(self, ws_url):
        self.ws_url = ws_url
        self.ws_client = YandexMusicWS(self, ws_url)
        threading.Thread(target=self.ws_client.run, daemon=True).start()