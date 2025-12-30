import os
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient

# =====================================================
# CONFIG
# =====================================================
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("❌ MONGO_URI not set")

DB_NAME = "trading"
COLLECTION_NAME = "daily_signals"

IST = timezone(timedelta(hours=5, minutes=30))

# =====================================================
# INIT
# =====================================================
app = Flask(__name__)
CORS(app)  # ✅ ENABLE CORS

client = MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]

# =====================================================
# HELPERS
# =====================================================
def today_ist():
    return datetime.now(IST).strftime("%Y-%m-%d")

# =====================================================
# API — FETCH SIGNALS BY DATE
# =====================================================
@app.route("/api/signals", methods=["GET"])
def get_signals():
    """
    Returns BUY signals from MongoDB for a given trade_date.
    If date not provided → uses today's IST date.
    If document not found → returns empty data.
    """

    requested_date = request.args.get("date") or today_ist()

    doc = collection.find_one({"trade_date": requested_date})

    # ❌ No document for this date
    if not doc:
        return jsonify({
            "requested_date": requested_date,
            "found": False,
            "count": 0,
            "data": []
        })

    buy_signals = doc.get("buy_signals", [])

    results = []
    for s in buy_signals:
        results.append({
            "symbol": s.get("symbol"),
            "open": s.get("open"),
            "entry": s.get("entry"),
            "target": s.get("target"),
            "stoploss": s.get("stoploss"),
            "qty": s.get("qty"),

            "entry_time": s.get("entry_time"),
            "exit_time": s.get("exit_time"),
            "hit": s.get("hit"),
            "pnl": s.get("pnl"),
            "status": s.get("status", "PENDING"),
        })

    return jsonify({
        "_id": str(doc.get("_id")),
        "trade_date": doc.get("trade_date"),
        "capital": doc.get("capital"),
        "margin": doc.get("margin"),
        "created_at": doc.get("created_at"),

        "requested_date": requested_date,
        "found": True,
        "count": len(results),
        "data": results
    })

# =====================================================
# HEALTH CHECK
# =====================================================
@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "MongoDB Signals API running 🚀"
    })

# =====================================================
# VERCEL ENTRY POINT
# =====================================================
# ❗ DO NOT use app.run()
# Vercel automatically serves the `app` object
