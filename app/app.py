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


PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#f7f7f2">
  <title>QuickBite | Good food, good mood</title>
  <style>
    :root{--ink:#202822;--muted:#748078;--line:#e8ebe4;--paper:#fff;--canvas:#f7f7f2;--green:#203a2d;--green2:#2e523d;--orange:#f2764b;--orange-dark:#d85f37;--lime:#d9e8b9;--shadow:0 18px 50px rgba(31,48,37,.08)}
    *{box-sizing:border-box}
    body{margin:0;background:var(--canvas);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}
    button,input{font:inherit}
    button{cursor:pointer}
    .shell{width:min(1160px,calc(100% - 48px));margin:0 auto}
    .topbar{height:78px;display:flex;align-items:center;justify-content:space-between;gap:24px}
    .brand{display:flex;align-items:center;gap:11px;text-decoration:none;color:var(--ink);font-size:20px;font-weight:850;letter-spacing:-.8px}
    .brand-mark{width:38px;height:38px;display:grid;place-items:center;border-radius:13px;background:var(--orange);color:#fff;font-size:21px;box-shadow:0 7px 16px rgba(242,118,75,.24)}
    .nav-links{display:flex;align-items:center;gap:30px;margin-left:auto;margin-right:16px}
    .nav-links a{color:#626e65;text-decoration:none;font-size:13px;font-weight:650}
    .nav-links a:hover{color:var(--orange-dark)}
    .delivery-pill{display:flex;align-items:center;gap:9px;padding:10px 14px;border:1px solid var(--line);border-radius:999px;background:#fff;color:#506056;font-size:12px;font-weight:700;white-space:nowrap}
    .delivery-dot{width:8px;height:8px;border-radius:50%;background:#68a56c;box-shadow:0 0 0 4px #eaf3e7}
    .hero{position:relative;overflow:hidden;min-height:350px;padding:48px 58px;border-radius:28px;background:linear-gradient(115deg,#20392d 0%,#294a36 61%,#365c40 100%);color:#fff;display:grid;grid-template-columns:1.1fr .9fr;align-items:center;box-shadow:var(--shadow)}
    .hero:before{content:"";position:absolute;width:350px;height:350px;border-radius:50%;right:10%;top:-180px;background:rgba(217,232,185,.08)}
    .hero-copy{position:relative;z-index:1;max-width:530px}
    .eyebrow{display:inline-flex;align-items:center;gap:9px;color:#d6e6c0;text-transform:uppercase;letter-spacing:1.7px;font-size:10px;font-weight:850}
    .eyebrow:before{content:"";width:22px;height:2px;background:var(--orange)}
    h1{max-width:520px;margin:18px 0 13px;font-size:clamp(42px,5.3vw,66px);line-height:.99;letter-spacing:-3.8px;font-weight:850}
    h1 span{color:#ff9a6c}
    .hero-copy p{max-width:430px;margin:0;color:#d3ddd3;font-size:15px;line-height:1.7}
    .hero-actions{display:flex;align-items:center;gap:17px;margin-top:27px}
    .primary-link{display:inline-flex;align-items:center;gap:12px;padding:13px 17px;border-radius:13px;background:var(--orange);color:#fff;text-decoration:none;font-size:13px;font-weight:800;box-shadow:0 9px 22px rgba(8,20,13,.18);transition:transform .18s,background .18s}
    .primary-link:hover{background:#ff8659;transform:translateY(-2px)}
    .hero-note{color:#d3ddd3;font-size:12px;font-weight:600}
    .hero-art{position:relative;z-index:1;justify-self:center;width:min(300px,100%);aspect-ratio:1;display:grid;place-items:center}
    .art-orbit{position:absolute;inset:8%;border:1px solid rgba(255,255,255,.2);border-radius:50%}
    .art-orbit:before,.art-orbit:after{content:"";position:absolute;border:1px solid rgba(255,255,255,.13);border-radius:50%;inset:11%}
    .art-orbit:after{inset:23%}
    .food-plate{position:relative;width:68%;aspect-ratio:1;display:grid;place-items:center;border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff8e6,#f3ddad 65%,#eacb8b);box-shadow:0 25px 42px rgba(7,20,12,.3),inset 0 0 0 13px rgba(255,255,255,.48);font-size:clamp(85px,11vw,135px);transform:rotate(-9deg)}
    .floating-label{position:absolute;padding:10px 14px;border:1px solid rgba(255,255,255,.38);border-radius:12px;background:rgba(255,255,255,.94);color:var(--ink);font-size:11px;font-weight:800;box-shadow:0 14px 28px rgba(0,0,0,.14)}
    .label-one{top:16%;right:-1%;transform:rotate(5deg)}
    .label-two{bottom:13%;left:0;transform:rotate(-5deg)}
    .content{padding:49px 0 58px}
    .section-head{display:flex;justify-content:space-between;align-items:end;gap:20px;margin-bottom:22px}
    .section-kicker{margin:0 0 8px;color:var(--orange-dark);font-size:10px;text-transform:uppercase;letter-spacing:1.6px;font-weight:850}
    h2{margin:0;font-size:30px;letter-spacing:-1.2px;line-height:1.1}
    .section-sub{margin:8px 0 0;color:var(--muted);font-size:13px}
    .fresh-note{display:flex;align-items:center;gap:8px;color:#68756d;font-size:12px;font-weight:650}
    .fresh-note span{font-size:17px}
    .order-layout{display:grid;grid-template-columns:minmax(0,1fr) 310px;gap:24px;align-items:start}
    .menu-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
    .food-card{overflow:hidden;background:var(--paper);border:1px solid #eceee8;border-radius:20px;transition:transform .2s,box-shadow .2s,border-color .2s}
    .food-card:hover{transform:translateY(-3px);box-shadow:0 14px 35px rgba(31,48,37,.09);border-color:#dde5d8}
    .food-art{height:138px;position:relative;display:grid;place-items:center;overflow:hidden;background:linear-gradient(140deg,#f7eee1,#f4e4d1)}
    .food-card:nth-child(4n+2) .food-art{background:linear-gradient(140deg,#e8efe2,#dce8d6)}
    .food-card:nth-child(4n+3) .food-art{background:linear-gradient(140deg,#f3e9d8,#eee0c5)}
    .food-card:nth-child(4n) .food-art{background:linear-gradient(140deg,#f4e7e4,#f1dcd4)}
    .food-art:before{content:"";position:absolute;width:128px;height:128px;border-radius:50%;background:rgba(255,255,255,.55);box-shadow:0 0 0 12px rgba(255,255,255,.2)}
    .food-emoji{position:relative;z-index:1;font-size:76px;line-height:1;filter:drop-shadow(0 10px 8px rgba(49,43,28,.14));transition:transform .25s}
    .food-card:hover .food-emoji{transform:scale(1.08) rotate(-4deg)}
    .food-tag{position:absolute;top:13px;left:13px;padding:6px 9px;border:1px solid rgba(255,255,255,.8);border-radius:999px;background:rgba(255,255,255,.8);color:#526155;font-size:9px;font-weight:850;letter-spacing:.65px;text-transform:uppercase}
    .food-info{padding:16px 17px 17px}
    .food-top{display:flex;align-items:start;justify-content:space-between;gap:10px}
    .food-title{margin:0;font-size:15px;font-weight:800;letter-spacing:-.35px}
    .food-price{color:var(--green2);font-size:14px;font-weight:850;white-space:nowrap}
    .food-desc{min-height:34px;margin:7px 0 15px;color:#7b857d;font-size:11px;line-height:1.55}
    .food-bottom{display:flex;justify-content:space-between;align-items:center;gap:12px}
    .food-category{color:#8b938c;font-size:10px;font-weight:700}
    .stepper{display:flex;align-items:center;gap:10px}
    .step-btn{width:30px;height:30px;display:grid;place-items:center;border:1px solid #e4e9e0;border-radius:10px;background:#fff;color:var(--green);font-size:17px;font-weight:700;line-height:1;transition:background .15s,border-color .15s}
    .step-btn:hover:not(:disabled){background:#edf4e8;border-color:#cbd9c4}
    .step-btn:disabled{cursor:not-allowed;opacity:.4}
    .qty-value{min-width:12px;text-align:center;font-size:12px;font-weight:800}
    .cart{position:sticky;top:20px;padding:22px;border:1px solid #e9ece6;border-radius:21px;background:#fff;box-shadow:0 12px 34px rgba(31,48,37,.055)}
    .cart-head{display:flex;align-items:center;justify-content:space-between;padding-bottom:16px;border-bottom:1px solid var(--line)}
    .cart-head h3{margin:0;font-size:16px;letter-spacing:-.4px}
    .cart-count{min-width:27px;height:27px;display:grid;place-items:center;padding:0 7px;border-radius:9px;background:#f4f5ef;color:#68746a;font-size:11px;font-weight:800}
    .cart-items{min-height:74px;padding:12px 0}
    .empty-cart{padding:11px 0;color:#929a92;font-size:12px;line-height:1.55}
    .cart-line{display:flex;justify-content:space-between;gap:12px;padding:8px 0;color:#536057;font-size:11px}
    .cart-line strong{color:var(--ink);font-size:11px}
    .cart-total{display:flex;justify-content:space-between;align-items:center;padding:14px 0 17px;border-top:1px solid var(--line);font-size:12px;color:#6e786f}
    .cart-total strong{color:var(--ink);font-size:19px;letter-spacing:-.5px}
    .customer-label{display:block;margin:0 0 7px;color:#68746a;font-size:10px;font-weight:800;letter-spacing:.3px}
    .customer-input{width:100%;height:43px;padding:0 12px;border:1px solid #e2e7df;border-radius:11px;outline:none;background:#fcfcfa;color:var(--ink);font-size:12px;transition:border .15s,box-shadow .15s}
    .customer-input:focus{border-color:#9bb68c;box-shadow:0 0 0 3px rgba(155,182,140,.18)}
    .checkout{width:100%;height:46px;margin-top:13px;border:0;border-radius:12px;background:var(--orange);color:white;font-size:12px;font-weight:850;box-shadow:0 8px 16px rgba(242,118,75,.18);transition:background .15s,transform .15s}
    .checkout:hover:not(:disabled){background:var(--orange-dark);transform:translateY(-1px)}
    .checkout:disabled{cursor:not-allowed;background:#d8ddd7;box-shadow:none;color:#89918a}
    .cart-footnote{margin:11px 0 0;color:#98a098;text-align:center;font-size:10px;line-height:1.5}
    .message{display:none;margin-top:13px;padding:12px;border-radius:12px;font-size:11px;line-height:1.55}
    .message.show{display:block}
    .message.success{background:#edf5e9;color:#315d38;border:1px solid #d5e8cf}
    .message.error{background:#fff0eb;color:#9d4329;border:1px solid #f3d3c8}
    .loading{grid-column:1/-1;padding:38px;border:1px dashed #dce2d8;border-radius:18px;color:#788379;text-align:center;font-size:13px}
    .footer{display:flex;justify-content:space-between;align-items:center;gap:20px;padding:20px 0 28px;border-top:1px solid #e8ebe4;color:#8a948b;font-size:10px}
    .footer-brand{color:#546158;font-weight:800;letter-spacing:.2px}
    .footer-version{padding:6px 9px;border:1px solid #e5e9e2;border-radius:8px;background:#fff;color:#718074;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:10px}
    @media(max-width:850px){.hero{padding:38px 38px;grid-template-columns:1fr .75fr}.hero-art{width:250px}.order-layout{grid-template-columns:minmax(0,1fr) 280px;gap:16px}.menu-grid{gap:12px}.food-info{padding:14px}.cart{padding:18px}}
    @media(max-width:680px){.shell{width:min(100% - 30px,520px)}.topbar{height:66px}.nav-links{display:none}.delivery-pill{font-size:10px;padding:9px 11px}.hero{min-height:0;padding:32px 24px 25px;border-radius:22px;grid-template-columns:1fr}.hero-copy{max-width:none}.hero-art{width:min(210px,70%);margin:18px auto 0}.food-plate{font-size:90px}.label-one{right:-5%}.label-two{left:-5%}h1{font-size:49px;letter-spacing:-2.8px}.hero-copy p{font-size:13px}.content{padding:35px 0 40px}.section-head{align-items:start;flex-direction:column;gap:12px}h2{font-size:27px}.order-layout{grid-template-columns:1fr}.menu-grid{gap:11px}.food-art{height:115px}.food-emoji{font-size:64px}.food-desc{min-height:50px}.cart{position:static;order:-1}.cart-items{min-height:0}.footer{align-items:flex-start;flex-direction:column;gap:10px}}
    @media(max-width:390px){.menu-grid{grid-template-columns:1fr}.food-art{height:145px}.food-desc{min-height:0}.hero-actions{align-items:flex-start;flex-direction:column;gap:11px}}
    @media(prefers-reduced-motion:reduce){*,*:before,*:after{scroll-behavior:auto!important;transition:none!important}}
  </style>
</head>
<body>
  <div class="shell">
    <header class="topbar">
      <a class="brand" href="#top" aria-label="QuickBite home"><span class="brand-mark">Q</span><span>quickbite</span></a>
      <nav class="nav-links" aria-label="Main navigation"><a href="#menu-section">Menu</a><a href="#order-panel">Your order</a></nav>
      <div class="delivery-pill"><span class="delivery-dot"></span> Freshly made · Ready in 25–35 min</div>
    </header>

    <main id="top">
      <section class="hero" aria-labelledby="hero-title">
        <div class="hero-copy">
          <div class="eyebrow">Fresh · fast · made for you</div>
          <h1 id="hero-title">Good food.<br><span>Good mood.</span></h1>
          <p>Big comfort, little wait. Pick a favorite, build your order, and let us take care of the rest.</p>
          <div class="hero-actions"><a class="primary-link" href="#menu-section">Explore the menu <span aria-hidden="true">↓</span></a><span class="hero-note">Simple, satisfying, delivered.</span></div>
        </div>
        <div class="hero-art" aria-hidden="true">
          <div class="art-orbit"></div><div class="food-plate">🍕</div>
          <div class="floating-label label-one">Made fresh ✨</div><div class="floating-label label-two">Your next favorite ☺</div>
        </div>
      </section>

      <section class="content" id="menu-section" aria-labelledby="menu-title">
        <div class="section-head">
          <div><p class="section-kicker">The good stuff</p><h2 id="menu-title">Find your feel-good food</h2><p class="section-sub">A few favorites, made for your kind of day.</p></div>
          <div class="fresh-note"><span aria-hidden="true">🌿</span> Made to order, always</div>
        </div>
        <div class="order-layout">
          <div class="menu-grid" id="menu" aria-live="polite"><div class="loading">Getting the menu ready…</div></div>
          <aside class="cart" id="order-panel" aria-labelledby="cart-title">
            <div class="cart-head"><h3 id="cart-title">Your order</h3><span class="cart-count" id="cart-count">0</span></div>
            <div class="cart-items" id="cart-items"><div class="empty-cart">Your picks will show up here.<br>Go on, choose something good.</div></div>
            <div class="cart-total"><span>Order total</span><strong id="cart-total">₹0</strong></div>
            <label class="customer-label" for="customer">NAME FOR THE ORDER</label>
            <input class="customer-input" id="customer" type="text" maxlength="80" placeholder="What should we call you?" autocomplete="name">
            <button class="checkout" id="checkout" type="button" disabled>Place my order</button>
            <p class="cart-footnote">Your total is calculated securely when you place the order.</p>
            <div class="message" id="message" role="status" aria-live="polite"></div>
          </aside>
        </div>
      </section>
    </main>

    <footer class="footer"><span class="footer-brand">quickbite · good food, easy days</span><span>Fresh picks. Happy bites.</span><span class="footer-version">version {{ version }}</span></footer>
  </div>
  <script>
    const menuEl = document.getElementById('menu');
    const cartEl = document.getElementById('cart-items');
    const countEl = document.getElementById('cart-count');
    const totalEl = document.getElementById('cart-total');
    const customerEl = document.getElementById('customer');
    const checkoutEl = document.getElementById('checkout');
    const messageEl = document.getElementById('message');
    const quantities = {};
    const details = {
      1: { icon: '🍕', category: 'Italian favorite', description: 'A classic tomato, basil and cheese combination.' },
      2: { icon: '🌯', category: 'Street-food favorite', description: 'Paneer tikka wrapped up with a little warmth.' },
      3: { icon: '🍛', category: 'Comfort bowl', description: 'A comforting bowl of fragrant rice and spices.' },
      4: { icon: '🥞', category: 'South Indian favorite', description: 'A golden, crisp dosa made for a proper meal.' },
      5: { icon: '🧋', category: 'Cool-down pick', description: 'A chilled coffee for your afternoon reset.' }
    };
    let menu = [];

    function money(value) { return '₹' + Number(value).toLocaleString('en-IN'); }
    function element(tag, className, text) {
      const node = document.createElement(tag);
      if (className) node.className = className;
      if (text !== undefined) node.textContent = text;
      return node;
    }
    function renderMenu() {
      menuEl.replaceChildren();
      if (!menu.length) {
        menuEl.append(element('div', 'loading', 'The menu is empty right now. Please check back soon.'));
        return;
      }
      menu.forEach((item) => {
        const info = details[item.id] || { icon: '🍽️', category: 'QuickBite favorite', description: 'A delicious pick for your next meal.' };
        const qty = quantities[item.id] || 0;
        const card = element('article', 'food-card');
        const art = element('div', 'food-art');
        art.setAttribute('aria-hidden', 'true');
        art.append(element('span', 'food-tag', info.category));
        art.append(element('span', 'food-emoji', info.icon));
        const body = element('div', 'food-info');
        const top = element('div', 'food-top');
        top.append(element('h3', 'food-title', item.name));
        top.append(element('span', 'food-price', money(item.price)));
        body.append(top);
        body.append(element('p', 'food-desc', info.description));
        const bottom = element('div', 'food-bottom');
        bottom.append(element('span', 'food-category', 'Served fresh'));
        const stepper = element('div', 'stepper');
        const minus = element('button', 'step-btn', '−');
        minus.type = 'button'; minus.setAttribute('aria-label', 'Remove one ' + item.name); minus.disabled = qty === 0;
        minus.addEventListener('click', () => setQuantity(item.id, -1));
        const value = element('span', 'qty-value', String(qty));
        value.setAttribute('aria-live', 'polite');
        const plus = element('button', 'step-btn', '+');
        plus.type = 'button'; plus.setAttribute('aria-label', 'Add one ' + item.name); plus.disabled = qty >= 20;
        plus.addEventListener('click', () => setQuantity(item.id, 1));
        stepper.append(minus, value, plus);
        bottom.append(stepper);
        body.append(bottom);
        card.append(art, body);
        menuEl.append(card);
      });
    }
    function setQuantity(id, delta) {
      quantities[id] = Math.max(0, Math.min(20, (quantities[id] || 0) + delta));
      renderMenu();
      renderCart();
      messageEl.className = 'message';
      messageEl.textContent = '';
    }
    function renderCart() {
      const picked = menu.filter((item) => (quantities[item.id] || 0) > 0);
      const count = picked.reduce((sum, item) => sum + quantities[item.id], 0);
      const total = picked.reduce((sum, item) => sum + item.price * quantities[item.id], 0);
      countEl.textContent = String(count);
      totalEl.textContent = money(total);
      cartEl.replaceChildren();
      if (!picked.length) {
        cartEl.append(element('div', 'empty-cart', 'Your picks will show up here.\nGo on, choose something good.'));
      } else {
        picked.forEach((item) => {
          const line = element('div', 'cart-line');
          line.append(element('span', '', quantities[item.id] + ' × ' + item.name));
          line.append(element('strong', '', money(item.price * quantities[item.id])));
          cartEl.append(line);
        });
      }
      checkoutEl.disabled = !count || !customerEl.value.trim();
      checkoutEl.textContent = checkoutEl.dataset.loading === 'true' ? 'Placing your order…' : 'Place my order';
    }
    async function placeOrder() {
      const customer = customerEl.value.trim();
      const items = menu.map((item) => ({ id: item.id, qty: quantities[item.id] || 0 })).filter((item) => item.qty > 0);
      if (!customer || !items.length) return;
      checkoutEl.dataset.loading = 'true';
      checkoutEl.disabled = true;
      checkoutEl.textContent = 'Placing your order…';
      messageEl.className = 'message';
      messageEl.textContent = '';
      try {
        const response = await fetch('/api/orders', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ customer, items })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'We could not place that order. Please try again.');
        messageEl.className = 'message success show';
        messageEl.textContent = 'Order confirmed! Your order number is ' + data.order_id + '. Total: ' + money(data.total) + '.';
      } catch (error) {
        messageEl.className = 'message error show';
        messageEl.textContent = error.message || 'Something went wrong. Please try again.';
      } finally {
        checkoutEl.dataset.loading = 'false';
        renderCart();
      }
    }
    customerEl.addEventListener('input', renderCart);
    checkoutEl.addEventListener('click', placeOrder);
    fetch('/api/menu')
      .then((response) => { if (!response.ok) throw new Error('Menu unavailable'); return response.json(); })
      .then((data) => { menu = data; renderMenu(); renderCart(); })
      .catch(() => { menuEl.replaceChildren(element('div', 'loading', 'We could not load the menu. Please refresh in a moment.')); });
  </script>
</body>
</html>
"""


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
