from flask import Flask, render_template, jsonify, request
from jenkins_helper import get_all_jobs_from_views, get_nodes, retry_job, reconnect_node
from scheduler import start_scheduler

app = Flask(__name__)
start_scheduler()

@app.route("/")
def index():
    jobs = get_all_jobs_from_views()
    nodes = get_nodes()
    return render_template("index.html", jobs=jobs, nodes=nodes)

@app.route("/retry", methods=['POST'])
def retry():
    job_name = request.form['job_name']
    view_name = request.form['view_name']
    message = retry_job(view_name, job_name)
    return jsonify({"message": message})

@app.route("/reconnect", methods=['POST'])
def reconnect():
    node_name = request.form['node_name']
    message = reconnect_node(node_name)
    return jsonify({"message": message})

if __name__ == "__main__":
    app.run(debug=True)
