/*

Amber Engine

 */

// CONSTANTS
const titleObj = findByClass("intro--title"),
      imageObj = findByClass("intro--img"),
      inventoryObj = findByClass("body--inv__list"),
      locationsObj = findByClass("body--locations__list"),
      roomNameObj = findByClass("room--name"),
      roomImageObj = findByClass("room--image"),
      roomMessageObj = findByClass("room--topdetails"),
      roomDescriptionObj = findByClass("room--description");

// TODO temporary
// sectionFade(sections["section-loading"]);
// sectionFade(sections["section-intro"]);


// Prevents unloading before saving
/*
window.onbeforeunload = function (e) {
    e = e || window.event;
    // TODO check if game is saved

    if (e) {
        return e.returnValue = "Are you sure you want to exit the game?"
    }
    return "Are you sure you want to exit the game?"

};
*/

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
        console.debug("Sending action: " + action);

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
        this.sendAction("get-room", null, cb)
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
        this.sendAction("use-item", {item: item_id}, cb)
    }

    useDescriptionItem (item_id, cb) {
        this.sendAction("desc-use", {item: item_id}, cb)
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

function parseActionClass(action) {
    let act = action.action;
    let obj = action.obj;

    if (act === "add-to-inventory") {
        addToInventory(obj);
    }
    else if (act === "move-to") {

    }
}

// Useful functions
function sendDescriptionUse(self, item_id) {
    amber.useDescriptionItem(item_id, function (status, data) {
        console.log("Description item used");

        roomMessageObj.innerHTML = data.message;
    })
}

function sendInventoryUse(self, item_id) {
    amber.useItem(item_id, function (status, data) {
        console.log("Inventory item used");

        roomMessageObj.innerHTML = data.message;
    })
}

function moveToRoom(room_id) {
    amber.moveTo(room_id, function (status, data) {
        if (status === "forbidden") {
            roomMessageObj.innerHTML = data.message;
        }
        else {
            // Assume status is OK
            parseRoomAndSet(data);
        }
    });

    amber.getLocations(function (status, data) {
        console.log("Setting locations");

        let locations = data.locations;
        clearLocations();

        for (let i = 0; i < locations.length; i++) {
            addLocation(locations[i]);
        }
    })
}

function parseRoomAndSet(data) {
    roomNameObj.innerHTML = data.name;

    // Parses description
    let desc = data.description.text;

    let splits = desc.split(/({\w+\|\w+})/);
    for (let i = 0; i < splits.length; i++) {
        let str = splits[i];

        if (str.startsWith("{") && str.endsWith("}")) {

            // I know it's shit, thx
            let it = str.split("|");
            it = [it[0].replace("{", ""), it[1].replace("}", "")];

            let item_type = it[0];
            let item_id = it[1];

            let item_name = null;

            if (item_type === "room") {
                item_name = data.description.rooms[item_id].name;
            }
            else if (item_type === "item") {
                item_name = data.description.items[item_id].name;
            }

            assert(item_name !== null);

            splits[i]= "<span class='room--description__item' item-id='" + item_id + "' onclick='sendDescriptionUse(this, this.getAttribute(\"item-id\"))'>" + item_name + "</span>";
        }
    }

    roomDescriptionObj.innerHTML = splits.join("");
    roomMessageObj.innerHTML = data.msg;

    setImageSrc(roomImageObj, data.image);
}

function addToInventory(item) {
    let el = document.createElement("li");
    el.innerHTML = item.name;
    el.setAttribute("item-id", item.id);
    el.setAttribute("onclick", "sendInventoryUse(this, this.getAttribute(\"item-id\"))");

    inventoryObj.appendChild(el);
}

function addLocation(loc) {
    let el = document.createElement("li");
    el.innerHTML = loc.name;
    el.setAttribute("item-id", loc.id);
    el.setAttribute("onclick", "moveToRoom(this.getAttribute(\"item-id\"))");

    locationsObj.appendChild(el);
}

function clearLocations() {
    while (locationsObj.lastChild) {
        locationsObj.removeChild(locationsObj.lastChild);
    }
}

socket.onopen = function () {
    console.log("Websocket connected");
    amber.sendHandshake();

    // Gets intro and displays it
    amber.getIntro(function (status, data) {
        console.log("Setting intro");

        let title = data.title;
        let image = data.image;

        titleObj.innerHTML = title;
        imageObj.setAttribute("src", image);

        // Proceed to getting the first room data
        amber.getRoomInfo(function (status, data) {
            console.log("Setting initial room state");

            parseRoomAndSet(data);

            sectionFade(sections["section-loading"]);
            sectionFade(sections["section-intro"]);
        });

        amber.getInventory(function (status, data) {
            console.log("Setting inventory");

            let items = data.inventory;

            for (let i = 0; i < items.length; i++) {
                addToInventory(items[i]);
            }
        });

        amber.getLocations(function (status, data) {
            console.log("Setting locations");

            let locations = data.locations;

            for (let i = 0; i < locations.length; i++) {
                addLocation(locations[i]);
            }
        })

    })

};