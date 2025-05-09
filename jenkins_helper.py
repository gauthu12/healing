
import os
import json

TRACKER_FILE = "retry_tracker.json"
NODE_TRACKER_FILE = "node_tracker.json"

def load_tracker(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_tracker(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

retry_counts = load_tracker(TRACKER_FILE)
node_retry_counts = load_tracker(NODE_TRACKER_FILE)

def safe_get_json(resp, url):
    try:
        if resp.headers.get('Content-Type', '').startswith('application/json'):
            return resp.json()
        else:
            print(f"[ERROR] Non-JSON response from {url}")
            print(resp.text[:500])
            return {}
    except Exception as e:
        print(f"[EXCEPTION] Failed to parse JSON from {url}: {e}")
        print(resp.text[:500])
        return {}

import requests
from config import JENKINS_URL, USERNAME, API_TOKEN, PROXIES, VERIFY_SSL, TIMEOUT

REQUEST_KWARGS = {
    "auth": (USERNAME, API_TOKEN),
    "proxies": PROXIES,
    "verify": VERIFY_SSL,
    "timeout": TIMEOUT
}

from config import JENKINS_URL, USERNAME, API_TOKEN

auth = (USERNAME, API_TOKEN)
retry_counts = {}
node_retry_counts = {}

def get_all_jobs_from_views():
    jobs_list = []
    views_resp = requests.get(f"{JENKINS_URL}/api/json", **REQUEST_KWARGS).json()
    for view in views_resp.get('views', []):
        view_name = view['name']
        view_jobs_resp = requests.get(f"{JENKINS_URL}/view/{view_name}/api/json", **REQUEST_KWARGS).json()
        for job in view_jobs_resp.get('jobs', []):
            job_name = job['name']
            status, reason = get_job_status(view_name, job_name)
            jobs_list.append({
                "view": view_name,
                "name": job_name,
                "status": status,
                "retries": retry_counts.get(job_name, 0),
                "reason": reason or "-"
            })
    return jobs_list

def get_job_status(view, job):
    url = f"{JENKINS_URL}/view/{view}/job/{job}/lastBuild/api/json"
    resp = requests.get(url, **REQUEST_KWARGS)
    if resp.status_code == 200:
data = safe_get_json(resp, ")")
        return data.get('result', 'UNKNOWN'), data.get('description', '')
    return 'UNKNOWN', 'No data'

def retry_job(view, job_name):
    retry_counts[job_name] = retry_counts.get(job_name, 0) + 1
    save_tracker(TRACKER_FILE, retry_counts)
    if retry_counts[job_name] <= 3:
        requests.post(f"{JENKINS_URL}/view/{view}/job/{job_name}/build", **REQUEST_KWARGS)
        return f"Triggered retry for {job_name} (Attempt {retry_counts[job_name]}/3)"
    else:
        return f"Max retries reached for {job_name}"

def get_nodes():
    nodes_resp = requests.get(f"{JENKINS_URL}/computer/api/json", **REQUEST_KWARGS).json()
    nodes_list = []
    for node in nodes_resp.get('computer', []):
        nodes_list.append({
            "name": node['displayName'],
            "status": "Online" if node['offline'] == False else "Offline",
            "executors": f"{node['busyExecutors']}/{node['numExecutors']}",
            "last_connected": "-"
        })
    return nodes_list

def reconnect_node(node_name):
    node_retry_counts[node_name] = node_retry_counts.get(node_name, 0) + 1
    save_tracker(NODE_TRACKER_FILE, node_retry_counts)
    if node_retry_counts[node_name] <= 3:
        return f"Reconnect attempted for {node_name} (Mocked Attempt {node_retry_counts[node_name]}/3)"
    else:
        return f"Max reconnect attempts reached for {node_name}"
