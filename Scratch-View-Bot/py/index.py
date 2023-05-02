from requests import get, post, exceptions
from pymongo import MongoClient
from os import system, environ
from bs4 import BeautifulSoup
from datetime import datetime
from threading import Thread
from time import sleep, time
from sys import exit


proxy_failures = {}
proxies = []
new_proxies = []
old_proxies = []
unfiltered_proxies = []
proxy_list_set = False
views = 0
cycles = 0
errors = 0
start_time = time()
wait_time = 0
avg_wait = 0
last_request_time = start_time
views_since_update = 0
url = None
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "same-site",
    "Sec-GPC": "1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

if "mongodb_url" not in environ:
    exit("Please set the mongodb_url environment variable to your mongodb url")
elif environ["mongodb_url"] == "Change to your own mongodb url":
    exit("Please change the mongodb_url environment variable to your own mongodb url")
mongo = MongoClient(environ["mongodb_url"])["SC_Swarm"]

if "name" not in environ:
    exit("Please set the name environment variable to your chosen name for the worker")
elif environ["name"] == "Change to your own chosen name for the worker":
    exit(
        "Please change the name environment variable to your own chosen name for the worker"
    )
name = environ["name"]

worker = mongo["Workers"].find_one({"name": name})
if worker is None:
    mongo["Workers"].insert_one({"name": name, "viewsGenerated": 0})


def log(text):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")
    with open("output.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {text}\n")


def fetch():
    proxies_unfiltered = []
    try:
        for tr in (
            BeautifulSoup(
                get("https://free-proxy-list.net/", timeout=10).content, "html.parser"
            )
            .find("tbody")
            .find_all("tr")
        ):
            tds = tr.find_all("td")
            if len(tds) >= 2:
                proxies_unfiltered.append(
                    f"{tds[0].text.strip()}:{tds[1].text.strip()}"
                )
    except exceptions.ConnectionError:
        log("Failed to fetch free-proxy-list.net proxy list")
    return list(set(proxies_unfiltered))


def verify(proxies):
    global views, views_since_update, url
    results = {
        "res0": [],
        "res1": [],
        "res2": [],
        "res3": [],
        "res4": [],
        "combination": [],
        "success_count": {},
        "final": [],
    }
    intensity = 4
    for i in range(5):
        for proxy in proxies:
            try:
                response = post(
                    url,
                    headers=headers,
                    proxies={"https": proxy},
                    timeout=2,
                )
                if response.status_code == 200 and response.json() == {}:
                    views += 1
                    views_since_update += 1
                    results[f"res{i}"].append(proxy)
                    log(f"Success {i + 1}: {proxy}")
            except Exception as e:
                pass
        log(f"Finished {i + 1} round")
    results["combination"] = (
        results["res0"]
        + results["res1"]
        + results["res2"]
        + results["res3"]
        + results["res4"]
    )
    for proxy in results["combination"]:
        if proxy not in results["success_count"]:
            results["success_count"][proxy] = 1
        else:
            results["success_count"][proxy] += 1
    for key, value in results["success_count"].items():
        if value >= 4:
            results["final"].append(key)
    if len(results["final"]) <= 8:
        intensity = 3
        results["final"] = []
        for key, value in results["success_count"].items():
            if value >= 3:
                results["final"].append(key)
    return {"proxies": results["final"], "verification_intensity": intensity}


def proxy_list_updater(sleep_time_in_minutes=60):
    while True:
        global proxies, new_proxies, old_proxies, unfiltered_proxies, proxy_list_set, proxy_failures
        update_start_time = time()
        for proxy in proxy_failures.items():
            if proxy_failures[proxy] >= 15:
                try:
                    proxies.remove(proxy)
                except:
                    pass
        proxy_failures = {}
        log("Updating Proxy List")
        new_proxies = unfiltered_proxies = fetch()
        new_proxies = list(
            set([proxy for proxy in new_proxies if proxy not in old_proxies])
        )
        response = verify(new_proxies)
        verified_proxies = response["proxies"]
        for proxy in verified_proxies:
            proxies.append(proxy)
        proxies = list(
            set(
                [
                    proxy
                    for proxy in proxies
                    if proxy
                    not in [
                        proxy
                        for proxy in new_proxies + old_proxies
                        if proxy not in verified_proxies
                    ]
                ]
            )
        )
        proxies.append(None)
        proxies = list(set(proxies))
        old_proxies = list(
            set([proxy for proxy in unfiltered_proxies if proxy not in proxies])
        )
        log(
            f"\n        Added Proxies: {len(proxies)}"
            + f"\n        Current Proxy Count: {len(proxies)}"
            + f"\n        Update Time: {round((time() - update_start_time) / 60, 1)}min"
            + f"\n        Verification Intensity: {response['verification_intensity']}"
        )
        proxy_list_set = True
        sleep(sleep_time_in_minutes * 60)


config = mongo["Config"].find_one()
worker = mongo["Workers"].find_one({"name": name})
if worker is None:
    mongo["Workers"].insert_one({"name": name, "viewsGenerated": 0})
    worker = mongo["Workers"].find_one({"name": name})
url = config["url"]
cheacker_thread = Thread(target=proxy_list_updater)
cheacker_thread.start()

while True:
    if not proxy_list_set:
        continue
    elapsed_minutes = (time() - start_time) / 60
    system("clear")
    log(
        f"\n        Total View Count Increase: {views}"
        + f"\n        Total Cycles: {cycles}"
        + f"\n        Total Errors: {errors}"
        + f"\n        Elapsed Time (minutes): {round(elapsed_minutes, 1)}"
        + f"\n        Average View Count Increase per Minute: {round((views / elapsed_minutes if elapsed_minutes > 0 else 0), 2)}"
        + f"\n        Average Wait Time Between Requests (seconds): {round(avg_wait, 2)}"
    )
    config = mongo["Config"].find_one()
    views_since_update = 0
    if config["active"]:
        worker = mongo["Workers"].find_one({"name": name})
        mongo["Workers"].update_one(
            {"name": name},
            {"$set": {"viewsGenerated": views_since_update + worker["viewsGenerated"]}},
        )
        for proxy in proxies:
            wait_time = time() - last_request_time
            last_request_time = time()
            avg_wait = (avg_wait + wait_time) / 2
            try:
                response = post(
                    url, headers=headers, proxies={"https": proxy}, timeout=2
                )
                print(proxy, response.status_code, response.json())
                if response.status_code == 200 and response.json() == {}:
                    views += 1
                    views_since_update += 1
                else:
                    if proxy not in proxy_failures:
                        proxy_failures[proxy] = 1
                    else:
                        proxy_failures[proxy] += 1
            except exceptions.RequestException as e:
                errors += 1
                if proxy not in proxy_failures:
                    proxy_failures[proxy] = 1
                else:
                    proxy_failures[proxy] += 1
            except Exception as e:
                errors += 1
                if proxy not in proxy_failures:
                    proxy_failures[proxy] = 1
                else:
                    proxy_failures[proxy] += 1