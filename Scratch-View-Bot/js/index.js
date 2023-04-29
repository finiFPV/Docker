const {
    readFileSync,
    writeFileSync,
    existsSync
} = require('fs');
const {
    MongoClient
} = require('mongodb');

let mongoClient, url;
let active = false;
let frequency = 1000;
let views = 0;
let viewsSinceUpdate = 0;

const log = message => {
    const msg = `[ ${(new Date()).toISOString()} ] ${message}`
    writeFileSync(__dirname + "/output.log", msg + '\n' + readFileSync(__dirname + "/output.log"));
    console.log(msg);
}

const sendReqeuest = async () => {
    fetch(url, {
        credentials: "include",
        headers: {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "same-site",
            "Sec-GPC": "1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache"
        },
        referrer: "https://scratch.mit.edu/",
        method: "POST",
        mode: "cors"
    }).then(response => {
        if (response.status === 200) {
            views++;
            viewsSinceUpdate++
        };
        if (response.status !== 429) log(
            `Views Generated: ${views}, Latest Request Status: ${response.status}, Request Frequency: ${(frequency / 1000).toFixed(2)}s, Request URL: ${url}`
            )
    }).catch(error => log(error));
}

const init = async () => {
    if (process.env.MONGO_URL === undefined) throw new Error(
        "MONGO_URL environment variable not set, exiting.");
    else if (process.env.NAME === undefined) throw new Error(
        "NAME environment variable not set, exiting.");
    else if (process.env.MONGO_URL === "Change to your own mongodb url") throw new Error(
        "MONGO_URL environment variable not setup, exiting.");
    else if (process.env.NAME === "Change to your own worker's name") throw new Error(
        "NAME environment variable not setup, exiting.");
    if (!await existsSync(__dirname + "/output.log")) await writeFileSync(__dirname + "/output.log",
        "");
    const mongo = new MongoClient(process.env.MONGO_URL);
    await mongo.connect();
    mongoClient = mongo.db("SC_Swarm");
    const worker = await mongoClient.collection("Workers").findOne({
        name: process.env.NAME
    });
    if (worker === null) await mongoClient.collection("Workers").insertOne({
        name: process.env.NAME,
        viewsGenerated: 0
    });
    fetchData();
    setInterval(() => fetchData(), 60000);
    setInterval(() => {
        if (active) sendReqeuest();
    }, frequency);
};

const fetchData = async () => {
    const config = await mongoClient.collection("Config").findOne();
    const worker = await mongoClient.collection("Workers").findOne({
        name: process.env.NAME
    });
    await mongoClient.collection("Config").updateOne({}, {
        $set: {
            viewsGenerated: viewsSinceUpdate + config.viewsGenerated
        }
    });
    await mongoClient.collection("Workers").updateOne({
        name: process.env.NAME
    }, {
        $set: {
            viewsGenerated: viewsSinceUpdate + worker.viewsGenerated
        }
    });
    viewsSinceUpdate = 0;
    active = config.active;
    frequency = config.frequency;
    url = config.url;
    if (!active) log("Client is inactive, not sending requests.");
};

init();