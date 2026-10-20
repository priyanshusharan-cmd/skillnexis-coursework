const posts=[{title:'Learning by Building',category:'Learning',body:'Small projects make concepts concrete.'},{title:'A Better Debugging Habit',category:'Engineering',body:'Reproduce, isolate, and explain a bug.'},{title:'Designing for Small Screens',category:'Design',body:'Start with content and readable spacing.'}];
function Header(){return <header><h1>Field Notes</h1><p>Ideas from a learning developer</p></header>}
function Card({post}){return <article className="card"><small>{post.category}</small><h2>{post.title}</h2><p>{post.body}</p><button onClick={()=>alert('Demo action')}>Read more</button></article>}
function Footer(){return <footer>Week 1 React components demo</footer>}
function Button({children,onClick}){return <button onClick={onClick}>{children}</button>}
function Form({onSearch}){return <label>Search posts <input onChange={e=>onSearch(e.target.value)} placeholder="Search title or text" /></label>}
function App(){const [query,setQuery]=React.useState('');const visible=posts.filter(p=>(p.title+' '+p.body+' '+p.category).toLowerCase().includes(query.toLowerCase()));return <><Header/><main><Form onSearch={setQuery}/><div className="grid">{visible.map(p=><Card key={p.title} post={p}/>)}</div><p>{visible.length} post(s)</p><Button onClick={()=>setQuery('')}>Clear search</Button></main><Footer/></>}
ReactDOM.createRoot(document.getElementById('root')).render(<App/>);