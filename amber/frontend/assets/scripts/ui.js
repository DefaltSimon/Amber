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

// Fades a section in or out
function sectionFade(el, force_fade) {
    if ((fade_active === true) && (force_fade !== true)) {
        let time_delta = Math.abs(getTimeMs() - fade_target_time);

        setTimeout(sectionFade, time_delta, el);
        return
    }

    if (el === "undefined" || el === null) {
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


// HANDLES KEYPRESSES
let callbacks_press = {};
let callbacks_keydown = {};

function bindKey(key, cb) {
    callbacks_press[key] = cb;
}

// Should be used for characters only, this makes repeated calls when the button is down
function bindKeyChar(key, cb) {
    callbacks_keydown[key] = cb;
}

// Handles callbacks_press and _keydown
addEvent(document, "keypress", function (e) {
    e = e || window.event;

    let cb = callbacks_press[e.keyCode];
    if (typeof cb !== "undefined") {
        cb()
    }
});

addEvent(document, "keydown", function (e) {
    e = e || window.event;

    let cb = callbacks_keydown[e.keyCode];
    if (typeof cb !== "undefined") {
        cb()
    }
});

// Key constants
const ESCAPE = 27,
      ENTER = 13;


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


// MENU HANDLER
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

    setVolume(volume) {
        music.setVolume(volume);
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

// Game state configuration
class GameConfig {
    constructor () {
        // Sets defaults
        this.autoSave = true;
        this.playerName = null;
        this.soundVolume = 1;

        music.setVolume(this.soundVolume)
        // TODO this should include game saves
    }

    setVolume(volume) {
        this.soundVolume = volume;
        music.setVolume(volume);
    }
}
let config = new GameConfig();


// Keypress setup
// ENTER -> start game
// ESCAPE -> open menu
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

bindKeyChar(ESCAPE, handleMenu);


// PLAYER NAME input
const playerNameInput = findById("player-input"),
      playerNameLabel = findById("player-name"),
      playerSaveButton = findByClass("button--confirm"),
      playerVolumeSlider = findById("slider-volume"),
      playerAutosaveToggle = findById("autosave-toggle");

// Sets up the player name option
playerNameInput.innerHTML = config.playerName;
addEvent(playerNameInput, "focus", function () {
    playerNameLabel.innerHTML = "";
});


// Handles player name change
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

addEvent(playerVolumeSlider, "change", function () {
    let volume = parseFloat(playerVolumeSlider.value / 100);
    config.setVolume(volume);
});

addEvent(playerAutosaveToggle, "change", function () {
    logUI.debug("Autosave set to " + playerAutosaveToggle.checked);
    config.autoSave = playerAutosaveToggle.checked;
});