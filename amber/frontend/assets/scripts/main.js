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
let serverInfo = {};

class AmberFrontend {
    sendHandshake() {
        let data = {
            uiVersion: uiVersion
        };

        let cb = function (status, data) {
            serverInfo = data;
            logWS.debug("Handshake complete");
        };

        this.sendEvent("game/handshake", data, cb);
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
        this.sendAction("game/get/inventory", null, cb)
    }

    getIntro(cb) {
        this.sendAction("game/get/intro", null, cb)
    }

    getCurrentRoom(cb) {
        this.sendAction("room/get", null, cb)
    }

    getItemInfo(item_id, cb) {
        let payload = {
            "id": item_id
        };

        this.sendAction("item/get", payload, cb)
    }

    getLocations(cb) {
        this.sendAction("room/get/locations", null, cb)
    }

    enterRoom(room_id, cb) {
        this.sendAction("room/enter", {room: room_id}, cb)
    }

    combineItems(item1_id, item2_id, cb) {
        this.sendAction("inventory/combine", {item1: item1_id, item2: item2_id}, cb)
    }

    useItem(item_id, cb) {
        this.sendAction("inventory/use", {item: item_id}, cb)
    }

    useDescriptionItem (item_id, cb) {
        this.sendAction("room/use/description", {item: item_id}, cb)
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

    if (act === Action.add_item) {
        addToInventoryFromID(obj);
    }
    else if (act === Action.travel) {
        moveToRoom(obj);
    }
    else if (act === Action.remove_item) {
        refreshInventory();
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

function refreshInventory() {
    amber.getInventory(function (status, data) {
        logUI.log("Refreshing inventory");
        clearInventory();

        for (let i = 0; i < data.length; i++) {
            addToInventory(data[i]);
        }
    });
}

function sendInventoryUse(item_id) {
    amber.useItem(item_id, function (status, data) {
        logAction.log("Inventory item used");

        parseActionClass(data);

        roomMessageObj.innerHTML = data.message;
    })
}

function moveToRoom(room_id) {
    amber.enterRoom(room_id, function (status, data) {
        if (status === Status.FORBIDDEN) {
            roomMessageObj.innerHTML = data.message;
        }
        else {
            // Assume status is OK
            parseActionClass(data);

            _parseAndSetRoom(data);
            logAction.log("Moved to " + data.name);
        }
    });

    amber.getLocations(function (status, data) {
        clearLocations();
        for (let i = 0; i < data.length; i++) {
            addLocation(data[i]);
        }
    })
}

function _parseAndSetRoom(data) {
    if (typeof data["room"] !== typeof undefined) {
        data = data.room;
    }

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
    el.setAttribute("onclick", "sendInventoryUse(this.getAttribute(\"item-id\"))");

    inventoryObj.appendChild(el);
}

function addToInventoryFromID(item_id) {
    amber.getItemInfo(item_id, function (status, data) {
        if (status === Status.MISSING) {
            logUI.error("Missing item: " + item_id);
            return;
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

function clearInventory() {
    while (inventoryObj.lastChild) {
        inventoryObj.removeChild(inventoryObj.lastChild)
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
            console.debug(data);

            _parseAndSetRoom(data);

            sectionFade(sections["section-loading"]);
            sectionFade(sections["section-intro"]);
        });

        refreshInventory();

        amber.getLocations(function (status, data) {
            logUI.log("Setting locations");

            for (let i = 0; i < data.length; i++) {
                addLocation(data[i]);
            }
        })

    })

};