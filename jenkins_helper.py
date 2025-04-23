
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
        data = resp.json()
        return data.get('result', 'UNKNOWN'), data.get('description', '')
    return 'UNKNOWN', 'No data'

def retry_job(view, job_name):
    retry_counts[job_name] = retry_counts.get(job_name, 0) + 1
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
    if node_retry_counts[node_name] <= 3:
        return f"Reconnect attempted for {node_name} (Mocked Attempt {node_retry_counts[node_name]}/3)"
    else:
        return f"Max reconnect attempts reached for {node_name}"
