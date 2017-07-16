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

    let comp_style = getComputedStyle(el);
    let dur = comp_style["animationDuration"];
    let dur2 = comp_style["transitionDuration"];

    let duration = dur !== "0s" ? dur : dur2;
    duration = duration.replace("s", "") * 1000;

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
      TAB = 9;

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

bindKey(ESCAPE, function () {
    console.log("pressed ESCAPE");

    sectionFade(sections["section-menu"]);
});