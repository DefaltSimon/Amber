/*
Amber Keyhandler
 */
let elements = {};
function findById(id) {
    let el = document.getElementById(id);
    if (el != null) {
        elements[id] = el;
        return el
    }
    return null;
}
function findByClass(id) {
    let el = document.getElementsByClassName(id);
    if (el[0] !== null) {
        elements[id] = el[0];
        return el[0]
    }
    return null;
}

// Thanks SO
function addEvent(element, eventName, callback) {
    if (element.addEventListener) {
        element.addEventListener(eventName, callback, false);
    } else if (element.attachEvent) {
        element.attachEvent("on" + eventName, callback);
    } else {
        element["on" + eventName] = callback;
    }
}

let sections = {};

function updateSections() {
    let _sections = document.getElementsByClassName("game-section");

    for (i = 0; i < _sections.length; ++i) {
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
    if (cb != null) {
        cb()
    }
});

// Key constants
const ESCAPE = 27,
      ENTER = 13,
      TAB = 9;

// Keypress setup
bindKey(ENTER, function () {
    let introScreen = findById("section-intro");
    let gameScreen = findById("section-game");

    sectionFade(introScreen);
    sectionFade(gameScreen);
});