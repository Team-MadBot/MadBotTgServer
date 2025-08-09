// Authored by Kitori
// Made for MadBot Telegram
const tg = window.Telegram.WebApp;

const urlParams = new URLSearchParams(window.location.search);

const groupId = parseInt(urlParams.get("groupid"));
const initData = tg.initData;

const hCaptchaElement = document.getElementById("h-captcha");
const closeButtons = document.getElementsByClassName("close-button");

hCaptchaElement.setAttribute("data-theme", tg.colorScheme || "light");
tg.expand();

const loadingPage = document.getElementById("loading-page");
const captchaPage = document.getElementById("captcha-page");
const molodecPage = document.getElementById("molodec-page");
const tirobotPage = document.getElementById("tirobot-page");
const warningPage = document.getElementById("warning-page");

const acceptButton = document.getElementById('timerButton');
const buttonLoader = document.getElementById('button-loader');
const captchaLoader = document.getElementById('captcha-loader');

let countdownInterval;

function handleGroupInfo(data) {
    const pfp = document.getElementById("pfp");
    const name = document.getElementById("name");

    name.innerText = data.groupTitle;
    var imgSource = data.groupAvatarUrl;
    console.log(imgSource);
    new Promise((resolve, reject) => {
        pfp.src = imgSource;

        pfp.addEventListener("load", () => {
            resolve(pfp);
        });

        pfp.addEventListener("error", (error) => {
            generateLetterImage(data.groupTitle, tg.themeParams.button_color).then((url) => {
                pfp.src = url;
            });
            resolve(pfp);
        });
    }).then(result => {
        loadingPage.classList.remove("visible");
        captchaPage.classList.add("visible");
    });
}

function handleCaptchaSolve(hCaptchaResponse) {
    captchaLoader.classList.add("visible");
    const url = "https://tgbot.mxdcxt.xyz/api/submitcaptcha";
    const body = JSON.stringify({
        hCaptchaResponse,
        initData,
        groupId
    });
    const request = fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body
    });
    request.then((response) => {
        response.text().then((text) => {
            const data = JSON.parse(text);
            captchaLoader.classList.remove("visible");
            captchaPage.classList.remove("visible");
            if (data.status === "OK") {
                molodecPage.classList.add("visible");
            } else if (data.status === "IRL") {
                warningPage.classList.add("visible");
                initButton(JSON.parse(body));
            } else {
                tirobotPage.classList.add("visible");
            }
        });
    });
    request.catch(() => {
        captchaPage.classList.remove("visible");
        tirobotPage.classList.add("visible");
    });
}

function handleCloseButton() {
    tg.close();
}

for (const button of closeButtons) {
    button.addEventListener("click", handleCloseButton);
}

function getGroupInfo() {
    const url = "https://tgbot.mxdcxt.xyz/api/getgroupinfo";
    const body = JSON.stringify({
        initData,
        groupId
    });
    const request = fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body
    });
    request.then((response) => {
        response.text().then((text) => {
            if (response.status >= 400) {
                loadingPage.classList.remove("visible");
                tirobotPage.classList.add("visible");
            } else {
                const data = JSON.parse(text);
                handleGroupInfo(data);
            }
        });
    });
}

function generateLetterImage(title, background) { // da, made by ChatGPT
    return new Promise((resolve, reject) => {
        const canvas = document.createElement('canvas');
        canvas.width = 640;
        canvas.height = 640;
        const ctx = canvas.getContext('2d');

        // Заполняем фон
        ctx.fillStyle = background;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Настраиваем шрифт
        const letter = title.charAt(0).toUpperCase();
        ctx.fillStyle = 'white';
        ctx.font = 'normal 320px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        // Измеряем размеры текста
        const metrics = ctx.measureText(letter);
        const actualHeight = metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent;

        // Вычисляем позицию для центрирования
        const x = canvas.width / 2;
        const y = (canvas.height - actualHeight) / 2 + metrics.actualBoundingBoxAscent;

        // Рисуем букву
        ctx.fillText(letter, x + 8, y + 4);

        // Преобразуем canvas в PNG и возвращаем как Data URL
        canvas.toBlob((blob) => {
            if (blob) {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            } else {
                reject(new Error('Failed to create blob'));
            }
        }, 'image/png');
    });
}

function startCountdown() {
    countdownInterval = setInterval(() => {
        clearInterval(countdownInterval);
        acceptButton.classList.add('active');
        acceptButton.disabled = false;
        buttonLoader.classList.remove("visible");
        acceptButton.classList.remove("invisible");
        acceptButton.innerHTML = 'Хорошо';
    }, 10000);
}

function initButton(json_body) {
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }

    acceptButton.disabled = true;
    acceptButton.classList.remove('active');

    startCountdown();

    acceptButton.onclick = () => {
        if (!acceptButton.disabled) {
            json_body.irlAccepted = true;
            acceptButton.classList.add("invisible");
            buttonLoader.classList.add("visible");
            const url = "https://tgbot.mxdcxt.xyz/api/submitcaptcha";
            const body = JSON.stringify(json_body);
            const request = fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body
            });
            request.then((response) => {
                response.text().then((text) => {
                    const data = JSON.parse(text);
                    buttonLoader.classList.remove("visible");
                    warningPage.classList.remove("visible");
                    if (data.status === "OK") {
                        molodecPage.classList.add("visible");
                    } else if (data.status === "IRL") {
                        warningPage.classList.add("visible");
                        initButton(JSON.parse(body));
                    } else {
                        tirobotPage.classList.add("visible");
                    }
                });
            });
            request.catch(() => {
                warningPage.classList.remove("visible");
                tirobotPage.classList.add("visible");
            });
        }
    };
}

getGroupInfo();