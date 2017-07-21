/*
Amber Keyhandler
 */

let sections = {};

function updateSections() {
    let _sections = document.getElementsByTagName("section");

    for (let i = 0; i < _sections.length; ++i) {
        let item = _sections[i];

        sections[item.getAttribute("id")] = item;
    }
}
updateSections();

function getTimeMs() {
    return (new Date()).getTime() / 1000
}

function getElementTransTime(el) {
    let comp_style = getComputedStyle(el);
    let dur = comp_style["animationDuration"];
    let dur2 = comp_style["transitionDuration"];

    return (dur !== "0s" ? dur : dur2).replace("s", "") * 1000;
}

let fade_active = false;
let fade_target_time = getTimeMs();

function sectionFade(el, force_fade) {
    if ((fade_active === true) && (force_fade !== true)) {
        let time_delta = Math.abs(getTimeMs() - fade_target_time);

        setTimeout(function () {
            sectionFade(el);
        }, time_delta );
        return
    }

    if (el === "undefined") {
        return
    }

    el.classList.toggle("active");

    let duration = getElementTransTime(el);

    if (el.classList.contains("nodisplay")) {
        el.classList.remove("nodisplay");
    }
    else {
        fade_active = true;

        let real_dur = duration / 1000;
        fade_target_time = getTimeMs() + real_dur;

        setTimeout(function () {
            el.classList.toggle("nodisplay");
            fade_active = false;

        }, duration)
    }
}

let callbacks = {};
function bindKey(key, cb) {
    callbacks[key] = cb;
}

addEvent(document, "keypress", function (e) {
    e = e || window.event;

    let cb = callbacks[e.keyCode];
    if (typeof cb !== "undefined") {
        cb()
    }
});

addEvent(document, "keydown", function (e) {
    e = e || window.event;

    let cb = callbacks[e.keyCode];
    if (typeof cb !== "undefined") {
        cb()
    }
});

// Key constants
const ESCAPE = 27,
      ENTER = 13,
      P = 80;


// Menu helpers
let current_panel = null;

const panelParent = findByClass("menu--panels"),
      panelAbout = findById("panel-about"),
      panelOptions = findById("panel-options");

function fadePanel(el, close) {
    current_panel = el;

    el.classList.toggle("open");

    if (!panelParent.classList.contains("visible")) {
        panelParent.classList.toggle("visible")
    }
    else if (close === true) {
        panelParent.classList.remove("visible");
        current_panel = null;
    }
}

// MENU HANDLING
class Menu {
    openLoadGame () {
        // TODO
    }

    openSaveGame () {
        // TODO
    }

    openOptions () {
        if (current_panel === panelOptions) {
            this.closePanel();
            return
        }
        this.closePanel();

        if (panelOptions.classList.contains("open")) {
            fadePanel(panelOptions, true)
        }
        else {
            fadePanel(panelOptions);
        }
    }

    openAbout () {
        if (current_panel === panelAbout) {
            this.closePanel();
            return
        }
        this.closePanel();

        if (panelAbout.classList.contains("open")) {
            fadePanel(panelAbout, true)
        }
        else {
            fadePanel(panelAbout);
        }
    }

    closePanel () {
        if (current_panel !== null) {
            fadePanel(current_panel, true);
        }
    }

    exitGame () {
        // TODO
    }
}

let menu = new Menu();

// Used by the RESUME button
function autoCloseMenu() {
    menu.closePanel();
    if (current_panel === null) {
        sectionFade(sections['section-menu'])
    }
}

class GameConfig {
    constructor () {
        // Sets defaults
        this.autoSave = true;
        this.playerName = null;
    }
}

let config = new GameConfig();

// Keypress setup
function fadeToGame() {
    let introScreen = sections["section-intro"];
    let gameScreen = sections["section-game"];

    if (introScreen.classList.contains("nodisplay")) {
        return;
    }

    sectionFade(introScreen);
    sectionFade(gameScreen);
}

bindKey(ENTER, fadeToGame);

function handleMenu() {
    if (current_panel !== null) {
        menu.closePanel();
        return;
    }

    sectionFade(sections["section-menu"]);
}

bindKey(ESCAPE, handleMenu);


// PLAYER NAME input
const playerNameInput = findById("player-input"),
      playerNameLabel = findById("player-name"),
      playerSaveButton = findByClass("button--confirm");

// Sets up the player name option
playerNameInput.innerHTML = config.playerName;
addEvent(playerNameInput, "focus", function () {
    playerNameLabel.innerHTML = "";
});

function savePlayerName() {
    config.playerName = playerNameInput.value;
}

addEvent(playerNameInput, "input", function () {
    if (playerNameInput.value === config.playerName) {
        // Remove the save button if nothing is changed
        playerSaveButton.classList.remove("visible");
    }

    if (!playerSaveButton.classList.contains("visible")) {
        playerSaveButton.classList.toggle("visible");
    }
});

addEvent(playerSaveButton, "click", function () {
    savePlayerName();
    playerSaveButton.classList.remove("visible");
});