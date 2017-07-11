console.log("Connecting to " + host + ":" + port);

function dumps(obj) {
    return JSON.stringify(obj);
}

function loads(string) {
    return JSON.parse(string);
}

// Setup socket.io
let socket = new WebSocket("ws://" + host + ":" + port);

let socketQueueId = 0;
let socketQueueCallback = {};


function sendAction(action, data, callback) {
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

function sendHandshake(game_name) {
    let payload = {
        type: "event",
        event: "handshake",
        gameName: game_name,
        req_id: ++socketQueueId
    };
    let pl = dumps(payload);
    socketQueueCallback[socketQueueId] = function (status, data) {
        console.log("Response got!");
        console.log(status);
        console.log(data);

    };

    socket.send(pl)
}


socket.onopen = function () {
    console.log("Connected!");

    sendHandshake("test game");
};

socket.onmessage = function (evt) {
    let json = loads(evt.data);

    let c_id = json.req_id;
    let status = json.status;
    let data = json.data;

    // Callback for that particular message gets called
    socketQueueCallback[c_id](status, data);

};