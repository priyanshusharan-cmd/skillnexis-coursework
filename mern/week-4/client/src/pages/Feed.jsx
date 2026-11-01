import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { useAuth } from '../AuthContext.jsx';

const ago = iso => {
  const s = Math.max(1, Math.round((Date.now() - new Date(iso)) / 1000));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.round(s / 60)}m ago`;
  if (s < 86400) return `${Math.round(s / 3600)}h ago`;
  return new Date(iso).toLocaleDateString();
};

function Post({ post, me, onChange, onDelete }) {
  const [comment, setComment] = useState('');
  const [error, setError] = useState('');

  async function run(fn) {
    try {
      setError('');
      await fn();
    } catch (e) {
      setError(e.message);
    }
  }
  const like = () => run(async () => onChange(await api(`/posts/${post.id}/like`, { method: 'POST' })));
  const send = e => {
    e.preventDefault();
    if (!comment.trim()) return;
    run(async () => {
      onChange(await api(`/posts/${post.id}/comments`, { method: 'POST', body: { text: comment } }));
      setComment('');
    });
  };

  return (
    <article className="post">
      <header>
        <strong>{post.author.name}</strong> <span className="muted">{ago(post.createdAt)}</span>
        {post.author.id === me.id && <button className="link" onClick={() => run(async () => { await api(`/posts/${post.id}`, { method: 'DELETE' }); onDelete(post.id); })}>Delete</button>}
      </header>
      <p>{post.text}</p>
      <button className="like" aria-pressed={post.likedByMe} onClick={like}>{post.likedByMe ? '♥' : '♡'} {post.likeCount}</button>
      <ul>
        {post.comments.map(c => <li key={c.id}><strong>{c.author.name}</strong> {c.text}</li>)}
      </ul>
      <form className="row" onSubmit={send}>
        <input value={comment} onChange={e => setComment(e.target.value)} placeholder="Add a comment" aria-label={`Comment on post by ${post.author.name}`} maxLength={300} />
        <button>Reply</button>
      </form>
      {error && <p role="alert" className="error">{error}</p>}
    </article>
  );
}

export default function Feed() {
  const { user, logout } = useAuth();
  const [posts, setPosts] = useState([]);
  const [text, setText] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    api('/posts').then(setPosts).catch(e => (e.status === 401 ? logout() : setError(e.message)));
  }, []);

  async function publish(e) {
    e.preventDefault();
    setError('');
    if (!text.trim()) return setError('Write something first');
    try {
      const p = await api('/posts', { method: 'POST', body: { text } });
      setPosts([p, ...posts]);
      setText('');
    } catch (err) {
      setError(err.message);
    }
  }
  const replace = p => setPosts(posts.map(x => (x.id === p.id ? p : x)));

  return (
    <>
      <form className="card" onSubmit={publish}>
        <textarea value={text} onChange={e => setText(e.target.value)} placeholder="What's on your mind?" aria-label="New post" maxLength={500} rows={3} />
        <div className="row"><span className="muted">{text.length}/500</span><button>Post</button></div>
        {error && <p role="alert" className="error">{error}</p>}
      </form>
      {posts.map(p => <Post key={p.id} post={p} me={user} onChange={replace} onDelete={id => setPosts(posts.filter(x => x.id !== id))} />)}
      {posts.length === 0 && <p className="muted">No posts yet. Be the first.</p>}
    </>
  );
}
