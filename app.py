"""Local web interface for the welfare to payroll converter."""

from __future__ import annotations

import os

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

from converter import ConversionError, convert


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/convert")
def convert_upload():
    uploaded = request.files.get("file")
    if uploaded is None or not uploaded.filename:
        return jsonify({"error": "Seleziona il file del provider."}), 400
    try:
        result = convert(
            request.form.get("provider", ""),
            request.form.get("company", ""),
            request.form.get("period", ""),
            uploaded.filename,
            uploaded.read(),
        )
    except ConversionError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({
        "filename": result.filename,
        "content": result.content,
        "input_rows": result.input_rows,
        "converted_rows": result.converted_rows,
        "output_rows": result.output_rows,
        "issues": [issue.as_dict() for issue in result.issues],
    })


@app.errorhandler(RequestEntityTooLarge)
def file_too_large(_error):
    return jsonify({"error": "Il file supera il limite di 10 MB."}), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8000")))
