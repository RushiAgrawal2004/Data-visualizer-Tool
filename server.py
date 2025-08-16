from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
import os
from functools import wraps

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

from data_processing import Process_data


app = Flask(__name__, static_folder="web", static_url_path="/web")
app.config["JSON_SORT_KEYS"] = False
# Use an environment variable for the secret key in production
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "a-default-fallback-secret-key")

# Dummy user database
USERS = {"admin": "password"}

DATA_STORE: Dict[str, Process_data] = {}


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = data["username"]
        except:
            return jsonify({"message": "Token is invalid!"}), 401
        return f(current_user, *args, **kwargs)
    return decorated


def get_data_obj_or_400(token: Optional[str]) -> Process_data:
    if not token or token not in DATA_STORE:
        # Return 400 with a structured error
        raise ValueError("Invalid or missing token. Upload a CSV first.")
    return DATA_STORE[token]


@app.route("/")
def login_page() -> Any:
    return send_from_directory(app.static_folder, "login.html")


@app.route("/app")
def index() -> Any:
    """Serves the main application page."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/signup")
def signup_page() -> Any:
    return send_from_directory(app.static_folder, "signup.html")


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if username in USERS:
        return jsonify({"error": "Username already exists"}), 400

    USERS[username] = password
    return jsonify({"message": "User created successfully"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    auth = request.json
    if not auth or not auth.get("username") or not auth.get("password"):
        return jsonify({"error": "Missing credentials"}), 401

    username = auth["username"]
    password = auth["password"]

    if username in USERS and USERS[username] == password:
        token = jwt.encode({
            "username": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config["SECRET_KEY"], algorithm="HS256")
        return jsonify({"token": token})

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/upload", methods=["POST"])
@token_required
def upload(current_user) -> Any:
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file."}), 400

    try:
        data_obj = Process_data(file)
    except Exception as exc:  # pragma: no cover - surface error details
        return jsonify({"error": f"Failed to read CSV: {exc}"}), 400

    token = str(uuid.uuid4())
    DATA_STORE[token] = data_obj

    columns = data_obj.get_columns()
    numeric_columns = data_obj.get_numeric_columns()

    return jsonify({
        "token": token,
        "columns": columns,
        "numericColumns": numeric_columns,
    })


@app.route("/api/columns", methods=["GET"])
@token_required
def get_columns(current_user) -> Any:
    token = request.args.get("token")
    try:
        data_obj = get_data_obj_or_400(token)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({
        "columns": data_obj.get_columns(),
        "numericColumns": data_obj.get_numeric_columns(),
    })


@app.route("/api/preview", methods=["GET"])
@token_required
def preview(current_user) -> Any:
    token = request.args.get("token")
    try:
        data_obj = get_data_obj_or_400(token)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    df = data_obj.get_df()
    max_rows = min(500, len(df))
    preview_rows = df.head(max_rows)
    return jsonify({
        "columns": preview_rows.columns.tolist(),
        "rows": preview_rows.astype(str).values.tolist(),
        "rowCount": int(max_rows),
        "totalRows": int(len(df)),
    })


@app.route("/api/describe", methods=["GET"])
@token_required
def describe(current_user) -> Any:
    token = request.args.get("token")
    try:
        data_obj = get_data_obj_or_400(token)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    desc_df = data_obj.describe_data().iloc[1:, :].round(2)
    return jsonify({
        "index": desc_df.index.tolist(),
        "columns": desc_df.columns.tolist(),
        "data": desc_df.astype(str).values.tolist(),
    })


@app.route("/api/plot-data", methods=["POST"])
@token_required
def plot_data(current_user) -> Any:
    payload = request.get_json(silent=True) or {}
    token = payload.get("token")
    try:
        data_obj = get_data_obj_or_400(token)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    chart: str = payload.get("chart", "").lower()
    x_col: Optional[str] = payload.get("x")
    y_col: Optional[str] = payload.get("y")
    color_col: Optional[str] = payload.get("color")
    barmode: Optional[str] = payload.get("barmode")

    df = data_obj.get_df()

    def col_values(col_name: str) -> List[Any]:
        return df[col_name].tolist()

    if chart == "bar":
        if not x_col or not y_col:
            return jsonify({"error": "x and y are required for bar chart."}), 400
        # Aggregate like plotly express bar does (sum by x)
        work = df[[x_col, y_col]].copy()
        work[y_col] = data_obj._coerce_to_numeric(work[y_col])
        work = work[work[y_col].notna()]
        # Treat x as category for grouping
        work["__x_cat__"] = work[x_col].astype(str)
        grouped = work.groupby("__x_cat__")[y_col].sum().reset_index()
        mean_val = float(work[y_col].mean()) if len(work) else None
        return jsonify({
            "x": grouped["__x_cat__"].tolist(),
            "y": grouped[y_col].tolist(),
            "mean": mean_val,
            "barmode": (barmode or "group"),
        })

    if chart == "line":
        if not x_col or not y_col:
            return jsonify({"error": "x and y are required for line chart."}), 400
        work = df[[x_col, y_col]].copy()
        work[y_col] = data_obj._coerce_to_numeric(work[y_col])
        work = work[work[y_col].notna()]
        # Determine x type and sort accordingly
        x_series = work[x_col]
        x_dt = pd.to_datetime(x_series, errors='coerce', infer_datetime_format=True)
        if x_dt.notna().any() and x_dt.notna().sum() >= len(work) * 0.8:
            work = work.assign(__x__=x_dt)
            work = work.sort_values("__x__")
            x_out = work["__x__"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
        else:
            x_num = pd.to_numeric(x_series, errors='coerce')
            if x_num.notna().any() and x_num.notna().sum() >= len(work) * 0.8:
                work = work.assign(__x__=x_num)
                work = work.sort_values("__x__")
                x_out = work["__x__"].tolist()
            else:
                x_out = x_series.astype(str).tolist()
        mean_val = float(work[y_col].mean()) if len(work) else None
        return jsonify({
            "x": x_out,
            "y": work[y_col].tolist(),
            "mean": mean_val,
        })

    if chart == "scatter":
        if not x_col or not y_col:
            return jsonify({"error": "x and y are required for scatter plot."}), 400
        x_series = data_obj._coerce_to_numeric(df[x_col])
        y_series = data_obj._coerce_to_numeric(df[y_col])
        valid = x_series.notna() & y_series.notna()
        if color_col:
            groups = []
            for key, group in df.loc[valid].groupby(color_col):
                groups.append({
                    "name": str(key),
                    "x": data_obj._coerce_to_numeric(group[x_col]).tolist(),
                    "y": data_obj._coerce_to_numeric(group[y_col]).tolist(),
                })
            return jsonify({"series": groups})
        return jsonify({"x": x_series.loc[valid].tolist(), "y": y_series.loc[valid].tolist()})

    if chart == "histogram":
        if not x_col:
            return jsonify({"error": "x is required for histogram."}), 400
        base_series = data_obj._coerce_to_numeric(df[x_col])
        if color_col:
            series_by_group: Dict[str, List[Any]] = {}
            for key, group in df.groupby(color_col):
                s = data_obj._coerce_to_numeric(group[x_col])
                series_by_group[str(key)] = s[s.notna()].tolist()
            return jsonify({"series": [{"name": name, "x": values} for name, values in series_by_group.items()]})
        return jsonify({"x": base_series[base_series.notna()].tolist()})

    if chart == "pie":
        values_col: Optional[str] = payload.get("values") or y_col
        names_col: Optional[str] = payload.get("names") or x_col
        if not values_col or not names_col:
            return jsonify({"error": "values and names are required for pie chart."}), 400
        values_series = data_obj._coerce_to_numeric(df[values_col])
        valid = values_series.notna()
        # Aggregate by names (sum values per category)
        grouped = df.loc[valid].groupby(names_col)[values_col].apply(lambda s: data_obj._coerce_to_numeric(s).sum())
        return jsonify({
            "values": grouped.values.tolist(),
            "names": grouped.index.astype(str).tolist(),
        })

    if chart == "box":
        if not x_col or not y_col:
            return jsonify({"error": "x and y are required for box plot."}), 400
        y_series = data_obj._coerce_to_numeric(df[y_col])
        valid = y_series.notna()
        if color_col:
            series = []
            for key, group in df.loc[valid].groupby([x_col, color_col]):
                series.append({
                    "name": f"{key[0]} - {key[1]}",
                    "x": [str(key[0])] * len(group),
                    "y": data_obj._coerce_to_numeric(group[y_col]).tolist(),
                })
            return jsonify({"series": series})
        return jsonify({
            "x": df.loc[valid, x_col].astype(str).tolist(),
            "y": y_series.loc[valid].tolist(),
        })

    return jsonify({"error": f"Unsupported chart type: {chart}"}), 400


if __name__ == "__main__":
    # Run a dev server. In production, use a proper WSGI server
    app.run(host="0.0.0.0", port=8000, debug=True)


