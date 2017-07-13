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

const version = "0.1.0";

class AmberFrontend {
    sendHandshake() {
        let data = {
            uiVersion: version
        };

        let cb = function (status, data) {
            console.log("Handshake complete");
            console.log(data);
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

    getRoomInfo(cb) {
        this.sendAction("get-room-info", null, cb)
    }

    getLocations(cb) {
        this.sendAction("get-locations", null, cb)
    }
}

amber = new AmberFrontend();

socket.onopen = function () {
    console.log("Websocket connected");
    amber.sendHandshake();
};

socket.onmessage = function (evt) {
    let json = loads(evt.data);

    let c_id = json.req_id;
    let status = json.status;
    let data = json.data;

    // Callback for that particular message gets called
    socketQueueCallback[c_id](status, data);

};

const btn = document.getElementById("testbtn");
btn.onclick = function () {
    amber.getLocations(function (status, data) {
        console.log("Locations received!");
        console.log(data);
    })
};