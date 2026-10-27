"""QuickBite - a small food-ordering API for the Cloud DevOps capstone."""
import json
import logging
import os
import time
import uuid

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("quickbite")

VERSION = os.getenv("APP_VERSION", "dev")
ORDERS_TABLE = os.getenv("ORDERS_TABLE")

MENU = [
    {"id": 1, "name": "Margherita Pizza", "price": 249},
    {"id": 2, "name": "Paneer Tikka Roll", "price": 149},
    {"id": 3, "name": "Veg Biryani", "price": 199},
    {"id": 4, "name": "Masala Dosa", "price": 119},
    {"id": 5, "name": "Cold Coffee", "price": 99},
]
MENU_BY_ID = {m["id"]: m for m in MENU}

# DynamoDB when running in AWS, in-memory dict for local runs and unit tests.
_memory_orders = {}
_table = None
if ORDERS_TABLE:
    import boto3

    _table = boto3.resource("dynamodb").Table(ORDERS_TABLE)


def save_order(order):
    if _table is not None:
        _table.put_item(Item=order)
    else:
        _memory_orders[order["order_id"]] = order


def load_order(order_id):
    if _table is not None:
        return _table.get_item(Key={"order_id": order_id}).get("Item")
    return _memory_orders.get(order_id)


def log_event(event, **fields):
    """Structured (JSON) logs go to CloudWatch Logs via the awslogs driver."""
    log.info(json.dumps({"event": event, "version": VERSION, **fields}))


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QuickBite</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:560px;margin:2rem auto;padding:0 1rem;color:#222}
 h1{margin-bottom:.2rem} .sub{color:#666;margin-top:0}
 .row{display:flex;justify-content:space-between;align-items:center;padding:.6rem 0;border-bottom:1px solid #eee}
 input[type=number]{width:3.5rem} input[type=text]{width:100%;padding:.5rem;margin:1rem 0;box-sizing:border-box}
 button{background:#e4572e;color:#fff;border:0;padding:.7rem 1.2rem;border-radius:6px;font-size:1rem;cursor:pointer}
 #msg{margin-top:1rem;font-weight:600} footer{margin-top:2rem;color:#999;font-size:.8rem}
</style></head><body>
<h1>QuickBite</h1><p class="sub">Hot food, fast. Order below.</p>
<div id="menu">Loading menu...</div>
<input id="customer" type="text" placeholder="Your name">
<button onclick="order()">Place order</button>
<div id="msg"></div>
<footer>version {{ version }}</footer>
<script>
let menu=[];
fetch('/api/menu').then(r=>r.json()).then(m=>{menu=m;
 document.getElementById('menu').innerHTML=m.map(i=>
 '<div class="row"><span>'+i.name+' - Rs '+i.price+'</span><input type="number" min="0" max="20" value="0" id="q'+i.id+'"></div>').join('');});
function order(){
 const items=menu.map(i=>({id:i.id,qty:+document.getElementById('q'+i.id).value})).filter(i=>i.qty>0);
 fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({customer:document.getElementById('customer').value,items:items})})
 .then(r=>r.json()).then(d=>{document.getElementById('msg').textContent=d.order_id?
  'Order placed! ID: '+d.order_id+' (Rs '+d.total+')':'Error: '+d.error;});}
</script></body></html>"""


@app.get("/")
def index():
    return render_template_string(PAGE, version=VERSION[:7])


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/version")
def version():
    return jsonify(version=VERSION)


@app.get("/api/menu")
def menu():
    return jsonify(MENU)


@app.post("/api/orders")
def place_order():
    body = request.get_json(silent=True) or {}
    customer = str(body.get("customer", "")).strip()
    items = body.get("items")
    if not customer or not isinstance(items, list) or not items:
        return jsonify(error="customer and items are required"), 400

    lines, total = [], 0
    for item in items:
        try:
            item_id, qty = int(item["id"]), int(item["qty"])
        except (KeyError, TypeError, ValueError):
            return jsonify(error="invalid item"), 400
        if item_id not in MENU_BY_ID or not 1 <= qty <= 20:
            return jsonify(error="invalid item or quantity"), 400
        total += MENU_BY_ID[item_id]["price"] * qty
        lines.append({"id": item_id, "qty": qty})

    order = {
        "order_id": uuid.uuid4().hex[:8],
        "customer": customer,
        "items": lines,
        "total": total,
        "created_at": int(time.time()),
    }
    save_order(order)
    log_event("ORDER_PLACED", order_id=order["order_id"], total=total)
    return jsonify(order), 201


@app.get("/api/orders/<order_id>")
def get_order(order_id):
    order = load_order(order_id)
    if order is None:
        return jsonify(error="order not found"), 404
    return jsonify(order)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
