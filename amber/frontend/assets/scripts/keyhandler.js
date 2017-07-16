/*
Amber Keyhandler
 */

let sections = {};

function updateSections() {
    let _sections = document.getElementsByClassName("game-section");

    for (let i = 0; i < _sections.length; ++i) {
        let item = _sections[i];

        sections[item.getAttribute("id")] = item;
    }
}
updateSections();

function sectionFade(el) {
    if (el === "undefined") {
        return
    }

    el.classList.toggle("active");
    setTimeout(function () {
        el.classList.toggle("nodisplay")
    }, 900)
}

let callbacks = {};
function bindKey(key, cb) {
    callbacks[key] = cb;
}

addEvent(document, "keypress", function (e) {
    e = e || window.event;

    let cb = callbacks[e.keyCode];
    if (cb !== null) {
        cb()
    }
});

// Key constants
const ESCAPE = 27,
      ENTER = 13,
      TAB = 9;

// Keypress setup
bindKey(ENTER, function () {
    let introScreen = sections["section-intro"];
    let gameScreen = sections["section-game"];

    if (introScreen.classList.contains("nodisplay")) {
        return;
    }

    sectionFade(introScreen);
    sectionFade(gameScreen);
});