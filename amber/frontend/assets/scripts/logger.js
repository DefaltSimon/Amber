/*

Logging facility

 */

class Logger {
    constructor (name) {
        this.name = name;
    }

    _parse(message) {
        return "[" + this.name + "] " + message;
    }

    info(message) {
        console.info(this._parse(message))
    }

    log(message) {
        console.log(this._parse(message))
    }

    debug(message) {
        console.debug(this._parse(message))
    }

    warn(message) {
        console.warn(this._parse(message))
    }

    error(message) {
        console.error(this._parse(message))
    }
}