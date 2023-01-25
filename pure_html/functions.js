function selectedMode() {
    for (thing of document.getElementsByName("arrangement")) {
        if ((!isHidden(thing) && thing.checked)) {
            return thing.value
        }
    }
    return null
}

function isHidden(el) {
    return (el.offsetParent === null)
}

function timeformat(millisec) {
    secs = millisec / 1000
    hours = Math.floor(secs / 60 / 60)
    mins = Math.floor(secs / 60 % 60)
    secs = Math.floor(secs % 60)
    milli = Math.round(millisec /10 % 100)
    hours = hours.toString().padStart(2, 0)
    mins = mins.toString().padStart(2, 0)
    secs = secs.toString().padStart(2, 0)
    milli = milli.toString().padStart(2, 0)
    out = "{}:{}:{}.{}".format(hours, mins, secs, milli)
    return out
}

function sizeformat(num, suffix='B') {
    for (unit of ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']) {
        if (Math.abs(num) < 1024.0) {
            return "{} {}{}".format(num.toFixed(1), unit, suffix)
        }
        num /= 1024.0
    }
    return "{} {}{}".format(num.toFixed(1), 'Yi', suffix)
}

function prettify_details(data) {
    var data = JSON.parse(JSON.stringify(data))
    keylength = 0
    vallength = 0
    for (key in data) {
        if (key.toString().startsWith("__")) {
            delete data[key]
            continue
        }
        if (Number.isInteger(data[key]) || (Number(data[key]) === data[key] && (data[key] % 1 !== 0))) {
            // Int or float
            intpart = Math.floor(data[key])
            fracpart = Math.round(data[key] * 100 % 100)
            data[key] = "{}.{}".format(intpart.toString(), fracpart.toString().padStart(2, "0"))
        }
        keylength = Math.max(keylength, key.toString().length)
        vallength = Math.min(Math.max(vallength, data[key].toString().length), 200)
        data[key] = data[key].toString().match(/.{1,200}/g)
        // if (typeof data[key] === "object"){
        //     data[key] = [JSON.stringify(data[key])]
        // }
        // else {
        //     data[key] = data[key].toString().match(/.{1,200}/g)
        // }
    }
    out = []
    out.push("╔" + "═".repeat(keylength) + "╦" + "═".repeat(vallength) + "╗")
    for (key in data) {
        for (index in data[key]){
            curstr = "║"
            curstr += key.toString().padEnd(keylength)
            curstr += "║"
            curstr += data[key][index].toString().padStart(vallength)
            curstr += "║"
            out.push(curstr)
        }
    }
    out.push("╚" + "═".repeat(keylength) + "╩" + "═".repeat(vallength) + "╝")
    return out.join("<br />")
}
