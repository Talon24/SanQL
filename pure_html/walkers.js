function* walker(tree) {
    if (Array.isArray(tree)) {
        yield* postgres_walker(tree[0]["Plan"]);
    } else if ("query_block" in tree) {
        yield* mysql_walker(tree["query_block"]);
    } else {
        yield* vertica_walker(tree);
    }
}

function* postgres_walker(tree, parent = null, depth = 0) {
    var current = JSON.parse(JSON.stringify(tree));
    delete current["Plans"];
    if ("Actual Total Time" in current) {
        current["__cost"] = current["Actual Total Time"];
    } else {
        current["__cost"] = current["Total Cost"];
    }
    var name = current["Node Type"];
    if (name == "CTE Scan" && "CTE Name" in current) {
        name += " as {}".format(current["CTE Name"]);
    } else if (("Alias" in current)) {
        name += " as {}".format(current["Alias"]);
    } else if (("Subplan Name" in current)) {
        name += " for {}".format(current["Subplan Name"]);
    }
    if (depth == 0) {
        // name += " - Total Cost: {:15,.2f}".format(current["__cost"]);
        name += " - Total Cost: {}".format(current["__cost"].toLocaleString('en-US', { minimumFractionDigits: 2 }));
    }
    current["__label"] = name;
    // console.log(current["__cost"]);

    for (entry in current) {
        if (entry == "Time") {
            current[entry] = timeformat(current[entry]);
        }
    }
    for (entry in current) {
        if (entry == "Space Used") {
            var space = current[entry];  // Postgres returns space in KB
            current[entry] = "{} KiB".format(space);
            if (space >= 1024) {
                current[entry] += " - Approx. {}".format(sizeformat(space * 1000));
            }
        }
    }
    yield [current, parent, depth];
    if ("Plans" in tree) {
        for (plan of tree["Plans"]) {
            yield* postgres_walker(plan, current, depth + 1);
        }
    }
}

function prunejoin(dict_, list_, sep = ", ") {
    out = []
    for (key of list_) {
        if (key in dict_) {
            out.push(dict_[key]);
        }
    }
    return out.join(sep);
}

function* vertica_walker(tree, parent = null, depth = 0) {
    var current = JSON.parse(JSON.stringify(tree));
    delete current["INPUT"];
    delete current["Inner"];
    delete current["Outer"];
    delete current["MATERIALIZE"];
    delete current["MATERIALIZE_AT_OUPUT"];
    current["__cost"] = current["COST"];
    var name = prunejoin(current, ["PATH_NAME", "EXTRA"], sep = " - ");
    current["__label"] = name;
    yield [current, parent, depth];
    if ("INPUT" in tree) {
        yield* vertica_walker(tree["INPUT"], current, depth + 1);
    }
    if ("Inner" in tree) {
        yield* vertica_walker(tree["Inner"], current, depth + 1);
    }
    if ("Outer" in tree) {
        yield* vertica_walker(tree["Outer"], current, depth + 1);
    }
}

function* mysql_walker(tree, parent = null, depth = 0) {
    var current = JSON.parse(JSON.stringify(tree));
    for (key in current) {
        if (Number(current[key]) == current[key]) {
            current[key] = Number(current[key])
        }
    }

    var costs = 0;
    for (key in current["cost_info"]) {
        current["Cost - " + key] = current["cost_info"][key];
        // if (key.endsWith("cost")) {
        //     costs += Number(current["cost_info"][key])
        // }
    }
    // console.log(JSON.parse(JSON.stringify(current)))
    if ("possible_keys" in current) { current["possible_keys"] = current["possible_keys"].join(", "); }
    if ("used_columns" in current) { current["used_columns"] = current["used_columns"].join(", "); }

    if ("cost_info" in current && "query_cost" in current["cost_info"]) { costs = Number(current["cost_info"]["query_cost"]); }
    if ("read_cost" in current["cost_info"]) { costs += Number(current["cost_info"]["read_cost"]); }
    current["__cost"] = costs;
    var name = current["access_type"] ?? ""
    if ("table_name" in current) {
        name += " as " + current["table_name"];
    }
    if (depth == 0) {
        name += " - Total Cost: {}".format(current["__cost"].toLocaleString('en-US', { minimumFractionDigits: 2 }));
    }
    current["__label"] = name;

    if ("ordering_operation" in current) {
        for (let [key, val] of Object.entries(current["ordering_operation"])) {
            if (typeof val === "boolean" || typeof val === "string" || typeof val === "number") {
                current["Ordering: " + key] = val
            }
            else {
                current[key] = val
            }
        }
    }
    delete current["ordering_operation"];

    if ("duplicates_removal" in current) {
        for (let [key, val] of Object.entries(current["duplicates_removal"])) {
            if (typeof val === "boolean" || typeof val === "string" || typeof val === "number") {
                current["Distinct: " + key] = val
            }
            else {
                current[key] = val
            }
        }
    }
    delete current["duplicates_removal"];

    var viewable = JSON.parse(JSON.stringify(current));
    delete viewable["nested_loop"];
    delete viewable["optimized_away_subqueries"];
    delete viewable["materialized_from_subquery"];
    delete viewable["cost_info"];
    // delete viewable["used_columns"];

    yield [viewable, parent, depth];
    var container = current;
    if ("nested_loop" in container) {
        for (var entry of container["nested_loop"]) {
            yield* mysql_walker(entry["table"], viewable, depth + 1);
        }
    }
    if ("optimized_away_subqueries" in container) {
        for (entry of container["optimized_away_subqueries"]) {
            yield* mysql_walker(entry["query_block"]["table"], viewable, depth + 1);
        }
    }
    if ("materialized_from_subquery" in container) {
        for (entry of container["materialized_from_subquery"]) {
            yield* mysql_walker(entry["query_block"]["table"], viewable, depth + 1);
        }
    }
}
