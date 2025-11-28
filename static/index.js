let totalSeconds = 0;
let currentTitle = null;

// Функция для обновления HTML-странички
async function fetchTrack() {
    try {
        const res = await fetch("/current_track");
        const data = await res.json();
        
        // Сделано для оптимизации (не обновляется заголовок и авторы, если они не изменились)
        if (currentTitle != data.title){
            let title = data.title || "Неизвестный заголовок";
            if (title.length > 35){
                title = title.slice(0, 32) + "...";
            }
            document.getElementById("title").textContent = title;
            document.getElementById("authors").textContent = (data.authors || []).join(", ") || "Неизвестный исполнитель";  

            await flipEmbed();
            currentTitle = data.title
        }

        document.getElementById("time").textContent = `${data.time.current || "0:00"} / ${data.time.total || "0:00"}`;
        document.getElementById("thumbnail").src = data.thumbnail || "https://corpse.pw/pics/77fb2583d234436658662257b545d76c.jpg";

        const status = data.status || "playing";
        const overlay = document.getElementById("pausedOverlay");

        // Наложение значка паузы, если воспроизведение трека остановлено
        if (status === "paused") {
            overlay.style.opacity = 1;
        } else {
            overlay.style.opacity = 0;
        }
        
        const [minCur, secCur] = (data.time.current || "0:00").split(":").map(Number);
        const [minTotal, secTotal] = (data.time.total || "0:00").split(":").map(Number);
        const curSeconds = (minCur || 0) * 60 + (secCur || 0);
        totalSeconds = (minTotal || 0) * 60 + (secTotal || 0);
        const percent = totalSeconds ? (curSeconds / totalSeconds) * 100 : 0;
        document.getElementById("progress").style.width = percent + "%";

    } catch (e) {
        console.error("Ошибка fetchTrack:", e);
    }
}

setInterval(fetchTrack, 200);
fetchTrack();

const embed = document.getElementById("embed");
let rotation = 0;
let isFlipping = false;

// Функция для вращения эмбеда при смене трека
async function flipEmbed() {
    if (isFlipping) return;
    isFlipping = true
    rotation += 360;
    embed.style.transform = `rotateY(${rotation}deg)`;
    await new Promise(resolve => setTimeout(resolve, 600));
    isFlipping = false;
}
