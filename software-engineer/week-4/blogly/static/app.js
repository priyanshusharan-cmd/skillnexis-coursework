// Blogly web client. Vanilla JS: all user text is inserted with textContent, never innerHTML.
const $ = (sel, root = document) => root.querySelector(sel);
const state = { token: sessionStorage.getItem("blogly_token"), me: null, page: 1, pages: 0, q: "", liked: new Set() };
const PAGE_SIZE = 10;

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => t.classList.remove("show"), 2500);
}

async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth && state.token) headers.Authorization = `Bearer ${state.token}`;
  const res = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  if (res.status === 401 && state.token && auth) { setToken(null); toast("Session expired, please log in again"); }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    const msg = Array.isArray(d) ? d.map(e => `${e.loc.at(-1)}: ${e.msg}`).join("; ") : d || `Error ${res.status}`;
    throw new Error(res.status === 429 ? `${msg} (try again in ${res.headers.get("Retry-After")} s)` : msg);
  }
  return data;
}

function setToken(token) {
  state.token = token;
  token ? sessionStorage.setItem("blogly_token", token) : sessionStorage.removeItem("blogly_token");
  renderAuth();
}

async function renderAuth() {
  state.me = null;
  if (state.token) {
    try { state.me = await api("/users/me"); } catch { state.token = null; sessionStorage.removeItem("blogly_token"); }
  }
  $("#auth").hidden = !!state.me;
  $("#composer").hidden = !state.me;
  $("#logout").hidden = !state.me;
  $("#who").hidden = !state.me;
  $("#who").textContent = state.me ? `@${state.me.username}` : "";
  loadFeed();
}

$("#auth-form").addEventListener("submit", async e => {
  e.preventDefault();
  const action = e.submitter?.dataset.action || "login";
  const creds = { username: $("#username").value.trim(), password: $("#password").value };
  $("#auth-error").textContent = "";
  try {
    if (action === "register") { await api("/auth/register", { method: "POST", body: creds, auth: false }); toast("Account created"); }
    const { access_token } = await api("/auth/login", { method: "POST", body: creds, auth: false });
    $("#password").value = "";
    setToken(access_token);
  } catch (err) { $("#auth-error").textContent = err.message; }
});
$("#logout").addEventListener("click", () => setToken(null));

$("#post-form").addEventListener("submit", async e => {
  e.preventDefault();
  $("#post-error").textContent = "";
  try {
    await api("/posts", { method: "POST", body: { title: $("#post-title").value, body: $("#post-body").value } });
    $("#post-title").value = $("#post-body").value = "";
    state.page = 1;
    toast("Published");
    loadFeed();
  } catch (err) { $("#post-error").textContent = err.message; }
});

$("#search-form").addEventListener("submit", e => { e.preventDefault(); state.q = $("#search").value.trim(); state.page = 1; loadFeed(); });
$("#prev").addEventListener("click", () => { state.page--; loadFeed(); });
$("#next").addEventListener("click", () => { state.page++; loadFeed(); });
$("#show-new").addEventListener("click", () => { state.page = 1; loadFeed(); });

async function loadFeed() {
  const params = new URLSearchParams({ page: state.page, page_size: PAGE_SIZE });
  if (state.q) params.set("q", state.q);
  try {
    const data = await api(`/posts?${params}`, { auth: false });
    state.pages = data.pages;
    const feed = $("#feed");
    feed.replaceChildren(...data.items.map(renderPost));
    if (!data.items.length) {
      const li = document.createElement("li");
      li.className = "card";
      li.textContent = state.q ? `No posts match "${state.q}".` : "No posts yet. Write the first one!";
      feed.append(li);
    }
    $("#page-info").textContent = data.pages ? `Page ${data.page} of ${data.pages}` : "";
    $("#prev").disabled = state.page <= 1;
    $("#next").disabled = state.page >= data.pages;
    $("#new-banner").hidden = true;
  } catch (err) { toast(err.message); }
}

function renderPost(p) {
  const el = $("#post-tpl").content.firstElementChild.cloneNode(true);
  el.dataset.id = p.id;
  $(".title", el).textContent = p.title;
  $(".meta", el).textContent = `@${p.author} · ${new Date(p.created_at).toLocaleString()}${p.updated_at ? " · edited" : ""}`;
  $(".body", el).textContent = p.body;
  $(".likes", el).textContent = p.likes;
  setCommentCount(el, p.comments);
  const like = $(".like", el);
  like.setAttribute("aria-pressed", state.liked.has(p.id));
  like.addEventListener("click", async () => {
    if (!state.me) return toast("Log in to like posts");
    const on = like.getAttribute("aria-pressed") !== "true";
    try {
      await api(`/posts/${p.id}/like`, { method: on ? "PUT" : "DELETE" });
      on ? state.liked.add(p.id) : state.liked.delete(p.id);
      like.setAttribute("aria-pressed", on);
    } catch (err) { toast(err.message); }
  });
  const del = $(".delete", el);
  del.hidden = !(state.me && state.me.username === p.author);
  del.addEventListener("click", async () => {
    if (!confirm("Delete this post?")) return;
    try { await api(`/posts/${p.id}`, { method: "DELETE" }); el.remove(); toast("Deleted"); } catch (err) { toast(err.message); }
  });
  $(".toggle-comments", el).addEventListener("click", async () => {
    const box = $(".comment-box", el);
    box.hidden = !box.hidden;
    if (!box.hidden) loadComments(p.id, el);
  });
  $(".comment-form", el).addEventListener("submit", async e => {
    e.preventDefault();
    if (!state.me) return toast("Log in to comment");
    const input = $(".comment-input", el);
    try { await api(`/posts/${p.id}/comments`, { method: "POST", body: { body: input.value } }); input.value = ""; }
    catch (err) { toast(err.message); }
  });
  return el;
}

function setCommentCount(el, n) {
  $(".comments", el).textContent = n;
  $(".comments-word", el).textContent = n === 1 ? "comment" : "comments";
}

async function loadComments(postId, el) {
  const data = await api(`/posts/${postId}/comments?page_size=50`, { auth: false });
  $(".comment-list", el).replaceChildren(...data.items.map(commentItem));
}

function commentItem(c) {
  const li = document.createElement("li");
  const b = document.createElement("b");
  b.textContent = `@${c.author}`;
  li.append(b, document.createTextNode(c.body));
  return li;
}

// ---------------------------------------------------------------- real-time
function connect(delay = 1000) {
  const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
  const live = $("#live");
  let ping;
  ws.onopen = () => { live.textContent = "● live"; live.classList.add("on"); delay = 1000; ping = setInterval(() => ws.send("ping"), 25000); };
  ws.onclose = () => {
    live.textContent = "● reconnecting"; live.classList.remove("on"); clearInterval(ping);
    setTimeout(() => connect(Math.min(delay * 2, 30000)), delay);  // exponential back-off
  };
  ws.onmessage = ({ data }) => handleEvent(JSON.parse(data));
}

function handleEvent(ev) {
  const card = id => $(`#feed [data-id="${id}"]`);
  if (ev.type === "post_created") {
    if (state.me && ev.post.author === state.me.username) return;
    if (state.page === 1 && !state.q) {
      const el = renderPost(ev.post);
      el.classList.add("flash");
      $("#feed").prepend(el);
      const items = $("#feed").children;
      if (items.length > PAGE_SIZE) items[items.length - 1].remove();
    } else $("#new-banner").hidden = false;
    toast(`New post from @${ev.post.author}`);
  } else if (ev.type === "likes_changed") {
    const el = card(ev.post_id);
    if (el) $(".likes", el).textContent = ev.likes;
  } else if (ev.type === "comment_added") {
    const el = card(ev.comment.post_id);
    if (el) {
      setCommentCount(el, Number($(".comments", el).textContent) + 1);
      if (!$(".comment-box", el).hidden) $(".comment-list", el).append(commentItem(ev.comment));
    }
  } else if (ev.type === "post_deleted") {
    card(ev.post_id)?.remove();
  }
}

renderAuth();
connect();
