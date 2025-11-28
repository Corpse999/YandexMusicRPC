import http from 'http';

const targetPort = process.argv[2];
const targetApp = process.argv[3];

function getYandexMusicWs() {
  return new Promise((resolve, reject) => {
    http.get(`http://127.0.0.1:${targetPort}/json`, res => {
      let data = '';

      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const tabs = JSON.parse(data);

          const musicTab = tabs.find(t => t.url === targetApp);

          if (musicTab && musicTab.webSocketDebuggerUrl) {
            resolve(musicTab.webSocketDebuggerUrl);
          } else {
            reject(new Error('Яндекс Музыка не найдена или нет websocket\'а'));
          }
        } catch (e) {
          reject(new Error("Не удалось получить информацию: " + e.message));
        }
      });
    }).on('Ошибка:', reject);
  });
}

getYandexMusicWs(1337)
  .then(ws => console.log(ws))
  .catch(err => console.error("Ошибка:", err));
