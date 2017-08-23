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

// LOGGER setup
const logWS = new Logger("WebSocket"),
      logAction = new Logger("Action"),
      logUI = new Logger("UI");

// Setup the websocket
logWS.debug("Connecting to " + host + ":" + port);
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
            logWS.debug("Handshake complete");
        };

        this.sendEvent("handshake", data, cb);
    }

    sendAction(action, data, callback) {
        logWS.debug("Sending action: " + action);

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
        this.sendAction("get-inventory", null, cb)
    }

    getIntro(cb) {
        this.sendAction("get-intro", null, cb)
    }

    getCurrentRoom(cb) {
        this.sendAction("get-room", null, cb)
    }

    getItemInfo(item_id, cb) {
        let payload = {
            "id": item_id
        };

        this.sendAction("get-item", payload, cb)
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

let amber = new AmberFrontend();

// Send data to AmberFrontend instance or the respective callback
socket.onmessage = function (evt) {
    let json = loads(evt.data);

    let c_id = json.req_id;
    let status = json.status;
    let data = json.data;

    // Callback for that particular request gets called
    if (!(c_id in socketQueueCallback)) {
        return
    }

    socketQueueCallback[c_id](status, data);

};

function parseActionClass(action) {
    let act = action.action;
    let obj = action.object;

    if (act === Action.new_item) {
        addToInventoryFromID(obj);
    }
    else if (act === Action.to_room) {
        moveToRoom(obj);
    }
}

// Useful functions
function useDescriptionElement(self, item_id) {
    amber.useDescriptionItem(item_id, function (status, data) {
        logAction.log("Description item used");

        roomMessageObj.innerHTML = data.message;
        parseActionClass(data);
    })
}

function sendInventoryUse(self, item_id) {
    amber.useItem(item_id, function (status, data) {
        logAction.log("Inventory item used");

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
            logAction.log("Moved to " + data.name);

            _parseAndSetRoom(data);
        }
    });

    amber.getLocations(function (status, data) {
        let locations = data.locations;
        clearLocations();

        for (let i = 0; i < locations.length; i++) {
            addLocation(locations[i]);
        }
    })
}

function _parseAndSetRoom(data) {
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

            splits[i]= "<span class='room--description__item' item-id='" + item_id + "' onclick='useDescriptionElement(this, this.getAttribute(\"item-id\"))'>" + item_name + "</span>";
        }
    }

    roomDescriptionObj.innerHTML = splits.join("");
    roomMessageObj.innerHTML = data.msg;

    // Set up music
    if (data.sound !== null) {
        logUI.log("Playing sound: " + data.sound);
        music.playSound(data.sound);
    }

    logUI.debug("Setting room image: " + data.image);
    setImageSrc(roomImageObj, data.image);
}

function addToInventory(item) {
    let el = document.createElement("li");
    el.innerHTML = item.name;
    el.setAttribute("item-id", item.id);
    el.setAttribute("onclick", "sendInventoryUse(this, this.getAttribute(\"item-id\"))");

    inventoryObj.appendChild(el);
}

function addToInventoryFromID(item_id) {
    amber.getItemInfo(item_id, function (status, data) {
        if (status === Status.MISSING) {
            logUI.error("Missing item: " + item_id);
        }

        addToInventory(data.item)
    })
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
    logWS.log("Websocket connected");
    amber.sendHandshake();

    // Gets intro and displays it
    amber.getIntro(function (status, data) {
        logUI.log("Setting intro");

        let title = data.title;
        let image = data.image;
        let sound = data.sound;

        if (sound !== null && sound !== "None") {
            music.playSound(sound);
        }

        if (title !== null) {
            titleObj.innerHTML = title;
        }

        if (image !== null) {
            imageObj.setAttribute("src", image);
        }

        // Proceed to getting the first room info
        amber.getCurrentRoom(function (status, data) {
            logUI.log("Setting initial room state");

            _parseAndSetRoom(data);

            sectionFade(sections["section-loading"]);
            sectionFade(sections["section-intro"]);
        });

        amber.getInventory(function (status, data) {
            logUI.log("Setting inventory");

            let items = data.inventory;

            for (let i = 0; i < items.length; i++) {
                addToInventory(items[i]);
            }
        });

        amber.getLocations(function (status, data) {
            logUI.log("Setting locations");

            let locations = data.locations;

            for (let i = 0; i < locations.length; i++) {
                addLocation(locations[i]);
            }
        })

    })

};