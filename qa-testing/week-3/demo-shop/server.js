// Demo Shop: a small web app + REST API used as the system under test for QA week 3.
// No dependencies. Run: node server.js   (PORT=4300 by default, listens on 127.0.0.1)
const http = require('node:http');
const crypto = require('node:crypto');

const PORT = Number(process.env.PORT || 4300);
const USERS = { standard_user: 'demo-pass-123', locked_user: 'demo-pass-123' };
const LOCKED = new Set(['locked_user']);
const PRODUCTS = [
  { id: 1, name: 'Canvas Backpack', price: 29.99, stock: 12 },
  { id: 2, name: 'Steel Water Bottle', price: 15.5, stock: 30 },
  { id: 3, name: 'Wireless Mouse', price: 18.0, stock: 8 },
  { id: 4, name: 'Desk Lamp', price: 24.0, stock: 5 },
  { id: 5, name: 'Notebook Set', price: 9.5, stock: 40 },
];
const sessions = new Map(); // token -> { user, cart: Map<productId, qty> }
const orders = [];

const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const page = (title, body, user) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)} · Demo Shop</title>
<style>body{font-family:system-ui,sans-serif;max-width:760px;margin:24px auto;padding:0 16px}nav a{margin-right:12px}.error{color:#b00020}.item{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #ddd;padding:8px 0}input{margin:4px 0;padding:6px}button{padding:6px 12px}</style></head>
<body><nav>${user ? `<a id="nav-inventory" href="/inventory">Products</a><a id="nav-cart" href="/cart">Cart (<span id="cart-count">${cartCount(user)}</span>)</a><a id="logout" href="/logout">Log out</a>` : '<a href="/">Log in</a>'}</nav><h1>${esc(title)}</h1>${body}</body></html>`;
const cartCount = s => [...s.cart.values()].reduce((a, b) => a + b, 0);
const send = (res, code, body, type = 'text/html; charset=utf-8', headers = {}) => { res.writeHead(code, { 'Content-Type': type, ...headers }); res.end(body); };
const json = (res, code, obj) => send(res, code, JSON.stringify(obj), 'application/json');
const redirect = (res, to, headers = {}) => { res.writeHead(303, { Location: to, ...headers }); res.end(); };
const readBody = req => new Promise((resolve, reject) => {
  let d = '';
  req.on('data', c => { d += c; if (d.length > 1e5) { reject(new Error('too large')); req.destroy(); } });
  req.on('end', () => resolve(d));
});
const cookieToken = req => (req.headers.cookie || '').split(/;\s*/).map(p => p.split('=')).find(([k]) => k === 'sid')?.[1];
const bearer = req => (req.headers.authorization || '').replace(/^Bearer\s+/i, '');

function login(username, password) {
  if (!username) return { error: 'Username is required' };
  if (!password) return { error: 'Password is required' };
  if (USERS[username] !== password) return { error: 'Username and password do not match' };
  if (LOCKED.has(username)) return { error: 'This user has been locked out' };
  const token = crypto.randomBytes(18).toString('hex');
  sessions.set(token, { user: username, cart: new Map() });
  return { token };
}
function validateCheckout({ firstName = '', lastName = '', email = '', postalCode = '' }) {
  const errors = [];
  if (!firstName.trim()) errors.push('First name is required');
  if (!lastName.trim()) errors.push('Last name is required');
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.push('Enter a valid email address');
  if (!/^\d{6}$/.test(postalCode)) errors.push('PIN code must be 6 digits');
  return errors;
}
function addToCart(s, productId, qty) {
  const p = PRODUCTS.find(x => x.id === productId);
  if (!p) return { code: 404, error: 'Product not found' };
  if (!Number.isInteger(qty) || qty < 1 || qty > 10) return { code: 400, error: 'Quantity must be a whole number from 1 to 10' };
  const next = (s.cart.get(productId) || 0) + qty;
  if (next > p.stock) return { code: 409, error: `Only ${p.stock} in stock` };
  s.cart.set(productId, next);
  return { code: 200 };
}
const cartView = s => {
  const items = [...s.cart].map(([id, qty]) => { const p = PRODUCTS.find(x => x.id === id); return { productId: id, name: p.name, price: p.price, qty, lineTotal: +(p.price * qty).toFixed(2) }; });
  return { items, total: +items.reduce((a, i) => a + i.lineTotal, 0).toFixed(2) };
};
function placeOrder(s, details) {
  const errors = validateCheckout(details);
  if (errors.length) return { code: 400, errors };
  if (!s.cart.size) return { code: 400, errors: ['Cart is empty'] };
  const order = { id: orders.length + 1, user: s.user, ...cartView(s), shipTo: { firstName: details.firstName, lastName: details.lastName, email: details.email, postalCode: details.postalCode } };
  for (const [id, qty] of s.cart) PRODUCTS.find(x => x.id === id).stock -= qty;
  orders.push(order); s.cart.clear();
  return { code: 201, order };
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  const p = url.pathname;
  try {
    // ---------- REST API ----------
    if (p.startsWith('/api/')) {
      if (p === '/api/health') return json(res, 200, { status: 'ok' });
      if (p === '/api/login' && req.method === 'POST') {
        let body; try { body = JSON.parse(await readBody(req) || '{}'); } catch { return json(res, 400, { error: 'Body must be JSON' }); }
        const r = login(body.username, body.password);
        return r.error ? json(res, 401, { error: r.error }) : json(res, 200, { token: r.token, user: body.username });
      }
      if (p === '/api/products' && req.method === 'GET') {
        const q = (url.searchParams.get('q') || '').toLowerCase();
        return json(res, 200, PRODUCTS.filter(x => x.name.toLowerCase().includes(q)));
      }
      const prod = p.match(/^\/api\/products\/(\d+)$/);
      if (prod && req.method === 'GET') {
        const x = PRODUCTS.find(y => y.id === Number(prod[1]));
        return x ? json(res, 200, x) : json(res, 404, { error: 'Product not found' });
      }
      const s = sessions.get(bearer(req));
      if (!s) return json(res, 401, { error: 'Missing or invalid token' });
      if (p === '/api/cart' && req.method === 'GET') return json(res, 200, cartView(s));
      if (p === '/api/cart' && req.method === 'POST') {
        let b; try { b = JSON.parse(await readBody(req) || '{}'); } catch { return json(res, 400, { error: 'Body must be JSON' }); }
        const r = addToCart(s, Number(b.productId), b.qty ?? 1);
        return r.error ? json(res, r.code, { error: r.error }) : json(res, 201, cartView(s));
      }
      const line = p.match(/^\/api\/cart\/(\d+)$/);
      if (line && req.method === 'PUT') {
        const id = Number(line[1]);
        if (!s.cart.has(id)) return json(res, 404, { error: 'Item not in cart' });
        let b; try { b = JSON.parse(await readBody(req) || '{}'); } catch { return json(res, 400, { error: 'Body must be JSON' }); }
        const qty = b.qty, stock = PRODUCTS.find(x => x.id === id).stock;
        if (!Number.isInteger(qty) || qty < 1 || qty > 10) return json(res, 400, { error: 'Quantity must be a whole number from 1 to 10' });
        if (qty > stock) return json(res, 409, { error: `Only ${stock} in stock` });
        s.cart.set(id, qty); return json(res, 200, cartView(s));
      }
      if (line && req.method === 'DELETE') {
        if (!s.cart.delete(Number(line[1]))) return json(res, 404, { error: 'Item not in cart' });
        return json(res, 200, cartView(s));
      }
      if (p === '/api/orders' && req.method === 'POST') {
        let b; try { b = JSON.parse(await readBody(req) || '{}'); } catch { return json(res, 400, { error: 'Body must be JSON' }); }
        const r = placeOrder(s, b);
        return r.errors ? json(res, r.code, { errors: r.errors }) : json(res, 201, r.order);
      }
      return json(res, 404, { error: 'Not found' });
    }

    // ---------- Web pages ----------
    const s = sessions.get(cookieToken(req));
    if (p === '/' && req.method === 'GET') {
      const err = url.searchParams.get('error');
      return send(res, 200, page('Log in', `${err ? `<p class="error" id="login-error" role="alert">${esc(err)}</p>` : ''}
<form id="login-form" method="post" action="/login" novalidate>
<label>Username <input id="username" name="username" autocomplete="username"></label><br>
<label>Password <input id="password" name="password" type="password" autocomplete="current-password"></label><br>
<button id="login-button" type="submit">Log in</button></form><p>Test user: standard_user / demo-pass-123</p>`));
    }
    if (p === '/login' && req.method === 'POST') {
      const f = new URLSearchParams(await readBody(req));
      const r = login(f.get('username'), f.get('password'));
      if (r.error) return redirect(res, '/?error=' + encodeURIComponent(r.error));
      return redirect(res, '/inventory', { 'Set-Cookie': `sid=${r.token}; Path=/; HttpOnly; SameSite=Lax` });
    }
    if (!s) return redirect(res, '/?error=' + encodeURIComponent('Please log in first'));
    if (p === '/logout') { sessions.delete(cookieToken(req)); return redirect(res, '/', { 'Set-Cookie': 'sid=; Path=/; Max-Age=0' }); }
    if (p === '/inventory' && req.method === 'GET') {
      const q = url.searchParams.get('q') || '';
      const list = PRODUCTS.filter(x => x.name.toLowerCase().includes(q.toLowerCase()));
      const flash = url.searchParams.get('msg');
      return send(res, 200, page('Products', `${flash ? `<p id="flash" role="status">${esc(flash)}</p>` : ''}
<form id="search-form" method="get" action="/inventory"><input id="search" name="q" value="${esc(q)}" placeholder="Search products"><button id="search-button">Search</button></form>
<p id="result-count">${list.length} product(s)</p>
${list.length ? list.map(x => `<div class="item" data-product-id="${x.id}"><span class="item-name">${esc(x.name)}</span><span class="item-price">₹${x.price.toFixed(2)}</span>
<form method="post" action="/cart/add"><input type="hidden" name="productId" value="${x.id}"><button class="add-to-cart" id="add-${x.id}">Add to cart</button></form></div>`).join('') : `<p id="no-results">No products match "${esc(q)}"</p>`}`, s));
    }
    if (p === '/cart/add' && req.method === 'POST') {
      const f = new URLSearchParams(await readBody(req));
      const r = addToCart(s, Number(f.get('productId')), Number(f.get('qty') || 1));
      return redirect(res, '/inventory?msg=' + encodeURIComponent(r.error || 'Added to cart'));
    }
    if (p === '/cart' && req.method === 'GET') {
      const v = cartView(s), err = url.searchParams.get('error');
      return send(res, 200, page('Your cart', `${err ? `<p class="error" id="cart-error" role="alert">${esc(err)}</p>` : ''}${v.items.length ? v.items.map(i => `<div class="item cart-item" data-product-id="${i.productId}"><span class="item-name">${esc(i.name)}</span>
<form method="post" action="/cart/update"><input type="hidden" name="productId" value="${i.productId}"><input class="qty" name="qty" type="number" value="${i.qty}" aria-label="Quantity for ${esc(i.name)}"><button class="update">Update</button></form>
<form method="post" action="/cart/remove"><input type="hidden" name="productId" value="${i.productId}"><button class="remove" id="remove-${i.productId}">Remove</button></form></div>`).join('') +
        `<p>Total: <strong id="cart-total">₹${v.total.toFixed(2)}</strong></p><a id="checkout" href="/checkout">Checkout</a>` : '<p id="empty-cart">Your cart is empty.</p>'}`, s));
    }
    if (p === '/cart/update' && req.method === 'POST') {
      const f = new URLSearchParams(await readBody(req)); const id = Number(f.get('productId')); const qty = Number(f.get('qty'));
      const stock = PRODUCTS.find(x => x.id === id)?.stock ?? 0;
      if (!Number.isInteger(qty) || qty < 1 || qty > 10) return redirect(res, '/cart?error=' + encodeURIComponent('Quantity must be a whole number from 1 to 10'));
      if (qty > stock) return redirect(res, '/cart?error=' + encodeURIComponent(`Only ${stock} in stock`));
      if (s.cart.has(id)) s.cart.set(id, qty);
      return redirect(res, '/cart');
    }
    if (p === '/cart/remove' && req.method === 'POST') { const f = new URLSearchParams(await readBody(req)); s.cart.delete(Number(f.get('productId'))); return redirect(res, '/cart'); }
    if (p === '/checkout' && req.method === 'GET') {
      return send(res, 200, page('Checkout', `<form id="checkout-form" method="post" action="/checkout" novalidate>
<label>First name <input id="first-name" name="firstName"></label><br><label>Last name <input id="last-name" name="lastName"></label><br>
<label>Email <input id="email" name="email" type="email"></label><br><label>PIN code <input id="postal-code" name="postalCode" inputmode="numeric"></label><br>
<button id="place-order" type="submit">Place order</button></form>`, s));
    }
    if (p === '/checkout' && req.method === 'POST') {
      const f = Object.fromEntries(new URLSearchParams(await readBody(req)));
      const r = placeOrder(s, f);
      if (r.errors) return send(res, 400, page('Checkout', `<ul id="checkout-errors" class="error" role="alert">${r.errors.map(e => `<li>${esc(e)}</li>`).join('')}</ul><p><a href="/checkout">Back to checkout</a> · <a href="/cart">Cart</a></p>`, s));
      return send(res, 200, page('Order placed', `<p id="order-confirmation">Thank you! Order #<span id="order-id">${r.order.id}</span> for ₹${r.order.total.toFixed(2)} is confirmed.</p>`, s));
    }
    return send(res, 404, page('Not found', '<p>Page not found.</p>', s));
  } catch (e) {
    return json(res, 500, { error: 'Internal error' });
  }
});
server.listen(PORT, '127.0.0.1', () => console.log(`Demo Shop on http://127.0.0.1:${PORT}`));
