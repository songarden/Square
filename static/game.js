// @ts-check
import StartToastifyInstance from "./toastify-es.js";

const GameState = {
    INIT: "init",
    PLAY: "play",
    REJECT: "reject",
    PAUSE: "pause",
    STOP: "stop",
    ALERT: "alert"
}

const GameEndResult = {
    SUCCESS: "success",
    FAILURE: "failure",
    ERROR: "error"
}

class GameContext {
    _state = GameState.INIT;
    /**
     * @type {number[]}
     */
    _scores = [];
    _remainingTime = 3000;
    _message = "";

    constructor() { }

    gameStart(callback) {
        this.state = GameState.PLAY;
        let intervalId = setInterval(() => {
            if (this._remainingTime - 10 > 0) {
                this._remainingTime -= 10;
            } else {
                clearInterval(intervalId);
                callback();
                return;
            }

            if (this.state !== GameState.PLAY) {
                clearInterval(intervalId);
                return;
            }
        }, 10);
    }

    gamePause() {
        this.state = GameState.PAUSE;
    }

    /**
     * 각 게임이 완료될 때 호출해야 합니다.
     * @param {((x1: number, y1: number, x2: number, y2: number) => number) | undefined} calc 점수를 계산하는 함수
     * @param {((x1: number, y1: number, x2: number, y2: number) => boolean) | undefined} rule 룰 위반을 계산하는 함수
     * @param {number} x1 첫번째 점의 X좌표
     * @param {number} y1 첫번째 점의 Y좌표
     * @param {number} x2 두번째 점의 X좌표
     * @param {number} y2 두번째 점의 Y좌표
     */
    gameEnd = (calc, rule, x1, y1, x2, y2) => {
        if (!rule) {
            console.error("gameEnd: rule is null.");
            this.state = GameState.REJECT;
            return GameEndResult.ERROR;
        }

        if (!calc) {
            console.error("gameEnd: calc is null.");
            this.state = GameState.REJECT;
            return GameEndResult.ERROR;
        }

        if (rule(x1, y1, x2, y2)) {
            this._scores.push(calc(x1, y1, x2, y2));
            this.state = GameState.INIT;
            console.log(this._scores);
            this._remainingTime = 3000;
            return GameEndResult.SUCCESS;
        } else {
            this.showMessage("다시 시도 해주세요.", 1000, () => {
                this.state = GameState.INIT;
            });

            return GameEndResult.FAILURE;
        }
    }

    /**
     * 게임을 중단합니다.
     */
    gameStop = () => {
        this.state = GameState.STOP;
    }

    showMessage = (message, milliseconds, callback) => {
        let prevState = this.state;
        this.state = GameState.ALERT;

        this._message = message;
        setTimeout(() => {
            this.state = prevState;
            if (callback) {
                callback();
            }
        }, milliseconds);
    }

    /**
     * 점수 배열의 얕은 복사를 반환합니다.
     */
    get scores() {
        return [...this._scores]
    }

    /**
     * 게임 상태를 반환합니다.
     */
    get state() {
        return this._state;
    }

    set state(gameState) {
        this._state = gameState;
    }
}

class Game {
    gameContext = new GameContext();
    /**
     * @type {CanvasRenderingContext2D | undefined | null}
     */
    renderingContext;
    /**
     * @type {undefined | ((x1: number, y1: number, x2: number, y2: number) => boolean)}
     */
    rule = undefined;
    /**
     * @type {undefined | ((x1: number, y1: number, x2: number, y2: number) => number)}
     */
    calc = undefined;
    startX = -1;
    startY = -1;
    endX = -1;
    endY = -1;
    maxGame = 3;
    drag = false;
    setting = (context) => { };

    constructor(rule, calc, canvas, setting, maxGame) {
        this.rule = rule;
        this.calc = calc;
        this.renderingContext = canvas?.getContext("2d");

        if (!this.renderingContext) {
            throw new Error("Failed to initialize the game.");
        }

        if (setting) {
            this.setting = setting;
            setting(this.renderingContext);
        }

        if (maxGame) {
            this.maxGame = maxGame;
        }
    }

    mouseUp = (e) => {
        this.drag = false;
        if (this.gameContext.state == GameState.PLAY) {
            if (this.startX === -1 || this.startY === -1 || this.endX === -1 || this.endY === -1) {
                this.gameContext.gameStop();
                this.gameContext.showMessage("마우스를 드래그 해주세요.", 1500, () => {
                    this.gameContext.showMessage("게임을 재시작합니다.", 1500, () => {
                        this.restart();
                    });
                });
                return;
            }

            this.gameContext.gameEnd(this.calc, this.rule, this.startX, this.startY, this.endX, this.endY);
            // request achievement
            const currentUser = window.location.href.split("/").filter(e => e).slice(-1);
            let scores = this.gameContext.scores;
            sendAchievement(`/arch/${currentUser}`, scores).then((response) => {
                if (!response['title'] || !response['body']) {
                    return;
                }
                notify(response['title'], response['body']);
            });

            if (scores.length === this.maxGame) {
                this.gameContext.gameStop();
                const sendResult = async () => {
                    let result = await sendResultData(`/send_result/${currentUser}`, scores);
                    if (result) {
                        console.log("서버에 점수를 보냈습니다.");
                        window.location.href = `/ranking/${currentUser}`;
                    } else {
                        alert("결과를 서버에 전송하는데 실패하였습니다.");
                        window.location.href = "/";
                    }
                }
                sendResult();
                return;
            }

            this.startX = -1;
            this.startY = -1;
            this.endX = -1;
            this.endY = -1;
            return;
        }

        console.error(`mouseUp:${this.gameContext.state}`);
        return;
    }

    mouseMove = (e) => {
        if (!this.drag) {
            return;
        }

        if (this.gameContext.state === GameState.PLAY) {
            this.endX = e.offsetX;
            this.endY = e.offsetY;
            return;
        }

        console.error(`mouseMove:${this.gameContext.state}`);
    }

    mouseDown = (e) => {
        if (this.gameContext.state === GameState.INIT || this.gameContext.state === GameState.REJECT) {
            this.startX = e.offsetX;
            this.startY = e.offsetY;
            this.gameContext.gameStart(() => {
                this.gameContext.showMessage("시간 초과!", 1500, () => {
                    this.restart();
                });
            });
            this.drag = true;
            return;
        }

        console.error(`mouseDown:${this.gameContext.state}`);
    }

    mouseOut = (e) => {
        console.log(`mouseOut`);
    }

    restart = () => {
        this.startX = -1;
        this.startY = -1;
        this.endX = -1;
        this.endY = -1;
        this.gameContext = new GameContext();
        this.drag = false;
        console.log("restart");
    }
}

/**
 * 씬을 그립니다.
 * @param {Game} game 
 */
function drawScene(game) {
    const context = game.renderingContext;
    if (!context) {
        console.error("Failed to get rendering context.");
        return;
    }

    const centerX = context.canvas.width / 2;
    const centerY = context.canvas.height / 2;
    switch (game.gameContext.state) {
        case GameState.INIT:
            context.fillText("START", centerX, centerY);
            break;
        case GameState.PLAY:
            context.fillText(`${game.gameContext._remainingTime / 10}`, centerX, centerY);
            if (game.startX === -1 || game.startY === -1 || game.endX === -1 || game.endY === -1) {
                break;
            }
            context.strokeRect(game.startX, game.startY, game.endX - game.startX, game.endY - game.startY);
            break;
        case GameState.STOP:
            context.fillText("STOP", centerX, centerY);
            break;
        case GameState.ALERT:
            context.fillText(`${game.gameContext._message}`, centerX, centerY);
            break;
    }
}

/**
 * 렌더링을 수행합니다.
 * @param {Game} game
 */
function render(game) {
    const context = game.renderingContext;
    if (!context) {
        console.error("Failed to render context.");
        return;
    }

    clearCanvas(context);
    drawScene(game);
    drawProgress(game);

    window.requestAnimationFrame(() => render(game));
}

/**
 * 현 컨텍스트를 지웁니다.
 * @param {CanvasRenderingContext2D} context 
 */
function clearCanvas(context) {
    context.clearRect(0, 0, context.canvas.width, context.canvas.height);
}

/**
 * 진행상황을 그립니다.
 * @param {Game} game 
 */
function drawProgress(game) {
    let scores = game.gameContext.scores;
    let context = game.renderingContext;

    function drawCircle(x, y, radius, color) {
        if (!context) {
            return;
        }

        context.beginPath();
        context.arc(x, y, radius, 0, 2 * Math.PI);
        context.fillStyle = color;
        context.fill();
        context.closePath();

        if (game.setting) {
            game.setting(context);
        }
    }

    function drawScore(x, y, text, color) {
        if (!context) {
            return;
        }

        context.fillStyle = color;
        context.font = "15px consolas";
        context?.fillText(text, x, y);

        if (game.setting) {
            game.setting(context);
        }
    }

    function drawCircleWithText(x, y, radius, text, circleColor, fontColor) {
        drawCircle(x, y, radius, circleColor);
        drawScore(x, y, text, fontColor);
    }

    const radius = 25;
    const pad = 10;
    const dx = 2 * radius + pad;
    const canvasX = game.renderingContext?.canvas.width;
    const height = radius + pad;

    if (!canvasX) {
        return;
    }

    let x = canvasX - game.maxGame * (dx);
    for (let i = game.maxGame - 1; i >= 0; i--) {
        if (scores[i] > 90) {
            drawCircleWithText(x, height, radius, `${scores[i].toFixed(2)}`, "green", "white");
        } else if (scores[i] > 70) {
            drawCircleWithText(x, height, radius, `${scores[i].toFixed(2)}`, "orange", "white");
        } else if (scores[i] > 0) {
            drawCircleWithText(x, height, radius, `${scores[i].toFixed(2)}`, "red", "white");
        } else {
            drawCircle(x, height, radius, "gray");
        }
        x -= dx;
    }
}

export function start() {
    let canvas = document.getElementById("canvas");
    const rule = function (x1, y1, x2, y2) {
        let dist = Math.sqrt(Math.pow(x1 - x2, 2) + Math.pow(y1 - y2, 2));
        return dist > 100;
    }

    const calc = function (x1, y1, x2, y2) {
        let lengthX = Math.abs(x2 - x1);
        let lengthY = Math.abs(y2 - y1);
        let score = Math.min(lengthX / lengthY, lengthY / lengthX) * 100;

        return score;
    }

    /**
     * @param {CanvasRenderingContext2D} context 
     */
    const setting = function (context) {
        context.lineWidth = 3;
        context.strokeStyle = "#000000";
        context.fillStyle = "#000000";
        context.font = "50px consolas";
        context.textAlign = "center";
    }

    let game = new Game(rule, calc, canvas, setting);
    canvas?.addEventListener("mouseup", (e) => game.mouseUp(e), false);
    canvas?.addEventListener("mousedown", (e) => game.mouseDown(e), false);
    canvas?.addEventListener("mousemove", (e) => game.mouseMove(e), false);
    canvas?.addEventListener("mouseout", (e) => game.mouseOut(e), false);

    window.requestAnimationFrame(() => render(game));
}

/**
 * 서버에 결과 데이터 POST 방식으로 보냅니다.
 * @param {string} url
 * @param {number[]} scores
 * 
 */
async function sendResultData(url, scores) {
    let requestData = JSON.stringify({ scores: scores });
    let result = await fetch(url, {
        method: "POST",
        headers: {
            'Accept': 'application/json, text/plain',
            'Content-Type': 'application/json;charset=UTF-8'
        },
        body: requestData
    });

    return result.ok;
}

async function sendAchievement(url, scores) {
    let requestData = JSON.stringify({ scores: scores });
    let result = await fetch(url, {
        method: "POST",
        headers: {
            'Accept': 'application/json, text/plain',
            'Content-Type': 'application/json;charset=UTF-8'
        },
        body: requestData
    });

    return await result.json();
}

const notify = (title, body) => {
    StartToastifyInstance({
        text: `업적 달성\n${title}\n ${body}`,
        duration: 3000,
        newWindow: true,
        close: true,
        gravity: "top", // `top` or `bottom`
        position: "right", // `left`, `center` or `right`
        stopOnFocus: true, // Prevents dismissing of toast on hover
        style: {
          background: "linear-gradient(to right, #00b09b, #96c93d)",
        },
      }).showToast();
}

start();
