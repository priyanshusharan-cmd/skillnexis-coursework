import { useEffect, useMemo, useState } from 'react';
import { api } from '../api.js';
import { useAuth } from '../AuthContext.jsx';

export default function Tasks() {
  const { logout } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState('');
  const [filter, setFilter] = useState('all');
  const [error, setError] = useState('');

  const guard = async fn => {
    try {
      setError('');
      await fn();
    } catch (e) {
      if (e.status === 401) logout();
      else setError(e.message);
    }
  };

  useEffect(() => { guard(async () => setTasks(await api('/tasks'))); }, []);

  const shown = useMemo(() => tasks.filter(t => (filter === 'all' ? true : filter === 'done' ? t.done : !t.done)), [tasks, filter]);

  const add = e => {
    e.preventDefault();
    if (!title.trim()) return;
    guard(async () => {
      const t = await api('/tasks', { method: 'POST', body: { title } });
      setTasks([t, ...tasks]);
      setTitle('');
    });
  };
  const toggle = t => guard(async () => {
    const u = await api(`/tasks/${t._id}`, { method: 'PUT', body: { done: !t.done } });
    setTasks(tasks.map(x => (x._id === u._id ? u : x)));
  });
  const remove = t => guard(async () => {
    await api(`/tasks/${t._id}`, { method: 'DELETE' });
    setTasks(tasks.filter(x => x._id !== t._id));
  });

  return (
    <section className="card">
      <h1>My tasks</h1>
      <form className="row" onSubmit={add}>
        <input value={title} onChange={e => setTitle(e.target.value)} placeholder="New task" aria-label="New task" maxLength={200} />
        <button>Add</button>
      </form>
      <div className="row filters">
        {['all', 'active', 'done'].map(f => (
          <button key={f} type="button" aria-pressed={filter === f} onClick={() => setFilter(f)}>{f}</button>
        ))}
        <span>{tasks.filter(t => !t.done).length} left</span>
      </div>
      {error && <p role="alert" className="error">{error}</p>}
      <ul>
        {shown.map(t => (
          <li key={t._id} className={t.done ? 'done' : ''}>
            <input type="checkbox" checked={t.done} onChange={() => toggle(t)} aria-label={`Mark ${t.title} done`} />
            <span>{t.title}</span>
            <button type="button" onClick={() => remove(t)} aria-label={`Delete ${t.title}`}>×</button>
          </li>
        ))}
      </ul>
      {shown.length === 0 && <p className="muted">Nothing here.</p>}
    </section>
  );
}
