function * walker(tree) {
    if (Array.isArray(tree)) {
        yield * postgres_walker(tree[0]["Plan"])
    } else if ("query_block" in tree) {
        yield * mysql_walker(tree["query_block"])
    } else {
        yield * vertica_walker(tree)
    }
}

function * postgres_walker(tree, parent=null, depth=0) {
    var current = JSON.parse(JSON.stringify(tree))
    delete current["Plans"]
    if ("Actual Total Time" in current) {
        current["__cost"] = current["Actual Total Time"]
    } else {
        current["__cost"] = current["Total Cost"]
    }
    var name = current["Node Type"]
    if (name == "CTE Scan" && "CTE Name" in current) {
        name += " as {}".format(current["CTE Name"])
    } else if (("Alias" in current)) {
        name += " as {}".format(current["Alias"])
    } else if (("Subplan Name" in current)) {
        name += " for {}".format(current["Subplan Name"])
    }
    if (depth == 0) {
        // name += " - Total Cost: {:15,.2f}".format(current["__cost"])
        name += " - Total Cost: {}".format(current["__cost"].toFixed(2))
    }
    current["__label"] = name
    // console.log(current["__cost"]);

    for (entry in current) {
        if (entry == "Time") {
            current[entry] = timeformat(current[entry])
        }
    }
    for (entry in current) {
        if (entry == "Space Used") {
            space = current[entry]  // Postgres returns space in KB
            current[entry] = "{} KiB".format(space)
            if (space >= 1024) {
                current[entry] += " - Approx. {}".format(sizeformat(space*1000))
            }
        }
    }
    yield [current, parent, depth]
    if ("Plans" in tree) {
        for (plan of tree["Plans"]) {
            yield * postgres_walker(plan, current, depth + 1)
        }
    }
}

function prunejoin(dict_, list_, sep=", "){
out = []
    for (key of list_) {
        if (key in dict_) {
            out.push(dict_[key])
        }
    }
    return out.join(sep)
}

function * vertica_walker(tree, parent=null, depth=0) {
    var current = JSON.parse(JSON.stringify(tree))
    delete current["INPUT"]
    delete current["Inner"]
    delete current["Outer"]
    delete current["MATERIALIZE"]
    delete current["MATERIALIZE_AT_OUPUT"]
    current["__cost"] = current["COST"]
    name = prunejoin(current, ["PATH_NAME", "EXTRA"], sep=" - ")
    current["__label"] = name
    yield [current, parent, depth]
    if ("INPUT" in tree) {
        yield * vertica_walker(tree["INPUT"], current, depth + 1)}
    if ("Inner" in tree) {
        yield * vertica_walker(tree["Inner"], current, depth + 1)}
    if ("Outer" in tree) {
        yield * vertica_walker(tree["Outer"], current, depth + 1)}
}

function * mysql_walker(tree, parent=null, depth=0) {
    var current = JSON.parse(JSON.stringify(tree))
    delete current["nested_loop"]
    delete current["used_columns"]
    costs = 0
    for (key in current["cost_info"]) {
        current["Cost - " + key] = current["cost_info"][key]
        if (key.endsWith("cost")) {
            costs += Number(current["cost_info"][key])
        }
    }
    current["__cost"] = costs
    delete current["cost_info"]
    name = current["table_name"]
    if (depth == 0) {
        name += " - Total Cost: {}".format(current["__cost"].toFixed(2))
    }
    current["__label"] = name
    yield [current, parent, depth]
    if ("nested_loop" in tree){
        for (entry of tree["nested_loop"]) {
            yield * mysql_walker(entry["table"], current, depth + 1)}
    }
}
