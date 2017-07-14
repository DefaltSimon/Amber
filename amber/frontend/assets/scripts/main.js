/*

Amber Engine

 */

// Utility functions
function dumps(obj) {
    return JSON.stringify(obj);
}
function loads(string) {
    return JSON.parse(string);
}



// Setup the websocket
console.log("Connecting to " + host + ":" + port);
let socket = new WebSocket("ws://" + host + ":" + port);

let socketQueueId = 0;
let socketQueueCallback = {};

// Basic communication
const uiVersion = "0.1.0";

class AmberFrontend {
    sendHandshake() {
        let data = {
            uiVersion: uiVersion
        };

        let cb = function (status, data) {
            console.log("Handshake complete");
        };

        this.sendEvent("handshake", data, cb);
    }

    sendAction(action, data, callback) {
        if (data === null) {
            data = {}
        }

        let payload = {
            type: "action",
            action: action,
            data: data,
            req_id: ++socketQueueId
        };
        let pl = dumps(payload);
        socketQueueCallback[socketQueueId] = callback;

        socket.send(pl);
    }

    sendEvent(event, data, callback) {
        let payload = {
            type: "event",
            event: event,
            data: data,
            req_id: ++socketQueueId
        };
        let pl = dumps(payload);
        socketQueueCallback[socketQueueId] = callback;

        socket.send(pl);
    }

    // Game methods
    getInventory(cb) {
        this.sendAction("get-inventory", null, cb);
    }

    getIntro(cb) {
        this.sendAction("get-intro", null, cb);
    }

    getRoomInfo(cb) {
        this.sendAction("get-room-info", null, cb)
    }

    getLocations(cb) {
        this.sendAction("get-locations", null, cb)
    }

    moveTo(room_id, cb) {
        this.sendAction("move-to", {room: room_id}, cb)
    }

    combineItems(item1_id, item2_id, cb) {
        this.sendAction("combine", {item1: item1_id, item2: item2_id}, cb)
    }

    useItem(item_id, cb) {
        this.sendAction("use", {item: item_id}, cb)
    }

    // TODO implement other endpoints
}

amber = new AmberFrontend();

socket.onmessage = function (evt) {
    let json = loads(evt.data);

    let c_id = json.req_id;
    let status = json.status;
    let data = json.data;

    // Callback for that particular message gets called
    if (!(c_id in socketQueueCallback)) {
        return
    }

    socketQueueCallback[c_id](status, data);

};

let buttons = {};

// Action setter
function setCallbackById(id, cb) {
    let item = document.getElementById(id);

    if (item === null) {
        console.error("No element with id " + id);
    }
    else {
        buttons[id] = item;
        item.onclick = cb;
        console.debug("Callback registered for " + id);
    }
}

socket.onopen = function () {
    console.log("Websocket connected");
    amber.sendHandshake();

    setCallbackById("testbtn", function () {
        amber.getLocations(function (status, data) {
            // TODO implement properly
            console.log("Locations received!");
            console.log(data);
        })
    });


    // Gets intro and displays it
    amber.getIntro(function (status, data) {
        console.log("Setting intro");

        let title = data.title;
        let image = data.image;

        let titleObj = findByClass("intro--title");
        let imageObj = findByClass("intro--img");

        titleObj.innerHTML = title;
        imageObj.setAttribute("src", image);

        sectionFade(sections["section-loading"]);
        sectionFade(sections["section-intro"]);
    })

};