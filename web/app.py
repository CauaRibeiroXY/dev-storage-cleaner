import os
import sys
from flask import Flask, render_template, jsonify, request

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from core.cleaner import StorageCleaner, check_the_sims_guard

app = Flask(__name__, template_folder=os.path.join(CURRENT_DIR, "templates"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/scan", methods=["GET"])
def api_scan():
    data = StorageCleaner.scan_all()
    return jsonify(data)

@app.route("/api/clean", methods=["POST"])
def api_clean():
    body = request.json or {}
    category = body.get("category")
    if category:
        res = StorageCleaner.clean_category(category)
        return jsonify({"result": res, "sims_guard": check_the_sims_guard()})
    else:
        res = StorageCleaner.clean_all()
        return jsonify(res)

@app.route("/api/guard", methods=["GET"])
def api_guard():
    return jsonify(check_the_sims_guard())

def run_web_app(port=5070):
    print(f"[*] Dev Storage Cleaner Dashboard ativo em http://localhost:{port}")
    app.run(debug=False, host="0.0.0.0", port=port)

if __name__ == "__main__":
    run_web_app()
