import { useEffect, useState } from 'react';
import { api } from '../api.js';

export default function Uploads() {
  const [items, setItems] = useState([]);
  const [preview, setPreview] = useState(null);
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => { api('/uploads').then(setItems).catch(e => setError(e.message)); }, []);
  useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview]);

  function pick(e) {
    const f = e.target.files[0];
    setError('');
    setFile(f || null);
    setPreview(f ? URL.createObjectURL(f) : null);
  }

  async function send(e) {
    e.preventDefault();
    if (!file) return setError('Choose an image first');
    setBusy(true);
    setError('');
    try {
      const form = new FormData();
      form.append('image', file);
      const saved = await api('/uploads', { method: 'POST', form });
      setItems([saved, ...items]);
      setFile(null);
      setPreview(null);
      e.target.reset();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h1>Images</h1>
      <form onSubmit={send}>
        <input type="file" accept="image/png,image/jpeg,image/gif,image/webp" onChange={pick} aria-label="Choose image" />
        {preview && <img className="preview" src={preview} alt="Selected preview" />}
        <button disabled={busy}>{busy ? 'Uploading...' : 'Upload'}</button>
      </form>
      {error && <p role="alert" className="error">{error}</p>}
      <div className="grid">
        {items.map(i => (
          <figure key={i.id}>
            <img src={i.url} alt={i.originalName} />
            <figcaption>{i.originalName}</figcaption>
          </figure>
        ))}
      </div>
      {items.length === 0 && <p className="muted">No images yet.</p>}
    </section>
  );
}
