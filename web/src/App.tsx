import { useEffect, useMemo, useRef, useState } from 'react'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import './index.css'
import { cardToPng, sharePng, savePdf } from './share'

type Node = { id: string; label: string }
type Chapter = { id: string; term: string; label: string; nodes: Node[] }
type Tree = { chapters: Chapter[]; item_types: string[] }
type Gold = {
  id: string
  stem: string
  options?: string[]
  knowledge_id: string
  knowledge_label: string
  item_type: string
  error_constraint: string
}
type TagOut = {
  knowledge_id: string
  knowledge_label: string
  item_type: string
  candidates: { knowledge_id: string; knowledge_label: string }[]
}
type Variant = { stem: string; constraint_ok: boolean; like?: boolean | null }

const dbName = 'cuoti-p0'

function saveLocal(key: string, value: unknown) {
  indexedDB.open(dbName, 1).onsuccess = (e) => {
    const db = (e.target as IDBOpenDBRequest).result
    if (!db.objectStoreNames.contains('kv')) return
    db.transaction('kv', 'readwrite').objectStore('kv').put(value, key)
  }
}

function openDb() {
  const req = indexedDB.open(dbName, 1)
  req.onupgradeneeded = () => {
    const db = req.result
    if (!db.objectStoreNames.contains('kv')) db.createObjectStore('kv')
  }
}

function texify(s: string) {
  return s
    .replace(/²/g, '^{2}')
    .replace(/³/g, '^{3}')
    .replace(/⁸/g, '^{8}')
    .replace(/√/g, '\\sqrt')
    .replace(/△/g, '\\triangle ')
    .replace(/∠/g, '\\angle ')
    .replace(/≤/g, '\\le ')
    .replace(/≥/g, '\\ge ')
    .replace(/±/g, '\\pm ')
    .replace(/≌/g, '\\cong ')
}

function MathText({ text }: { text: string }) {
  const html = useMemo(() => {
    try {
      return katex.renderToString(texify(text), {
        throwOnError: false,
        displayMode: false,
      })
    } catch {
      return text
    }
  }, [text])
  return <span className="stem" dangerouslySetInnerHTML={{ __html: html }} />
}

export default function App() {
  const [tree, setTree] = useState<Tree | null>(null)
  const [gold, setGold] = useState<Gold[]>([])
  const [page, setPage] = useState<'list' | 'tag' | 'var'>('list')
  const [cur, setCur] = useState<Gold | null>(null)
  const [tag, setTag] = useState<TagOut | null>(null)
  const [picked, setPicked] = useState<string>('')
  const [variants, setVariants] = useState<Variant[]>([])
  const [n, setN] = useState(3)
  const [picker, setPicker] = useState(false)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const cardRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    openDb()
    fetch('/api/tree').then((r) => r.json()).then(setTree)
    fetch('/api/gold').then((r) => r.json()).then(setGold)
  }, [])

  async function openItem(g: Gold) {
    setErr('')
    setCur(g)
    const r = await fetch('/api/tag', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stem: g.stem, options: g.options }),
    })
    const body = (await r.json()) as TagOut
    setTag(body)
    setPicked(body.knowledge_id)
    setPage('tag')
  }

  async function makeVariants() {
    if (!cur || !picked) return
    setErr('')
    const node = tree?.chapters.flatMap((c) => c.nodes).find((n) => n.id === picked)
    const r = await fetch('/api/variants', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        stem: cur.stem,
        knowledge_id: picked,
        error_constraint: cur.error_constraint,
        n,
      }),
    })
    const body = await r.json()
    const list: Variant[] = (body.variants || []).map((v: Variant) => ({
      ...v,
      like: true,
    }))
    setVariants(list)
    saveLocal(cur.id, { knowledge_id: picked, label: node?.label, variants: list })
    setPage('var')
  }


  async function sendCard(asPdf = false) {
    if (!cardRef.current || !cur || kept.length === 0) return
    setBusy(true)
    setErr('')
    try {
      const png = await cardToPng(cardRef.current)
      const base = `lianxika-${cur.id}`
      if (asPdf) await savePdf(png, base + '.pdf')
      else await sharePng(png, base + '.png')
    } catch (e) {
      setErr(e instanceof Error ? e.message : '分享失败')
    } finally {
      setBusy(false)
    }
  }

  const labelOf = (id: string) =>
    tree?.chapters.flatMap((c) => c.nodes).find((n) => n.id === id)?.label || id

  const kept = variants.filter((v) => v.like !== false)

  return (
    <div className="phone">
      {page === 'list' && (
        <>
          <div className="topbar">
            <div>
              <h1>错题本</h1>
              <p className="sub">评测集 v0.2 · 30 道金标</p>
            </div>
          </div>
          <div className="scroll">
            {gold.map((g) => (
              <div key={g.id} className="card item" onClick={() => openItem(g)}>
                <span className="id">{g.id}</span>
                <MathText text={g.stem} />
              </div>
            ))}
          </div>
        </>
      )}

      {page === 'tag' && cur && tag && (
        <>
          <div className="topbar">
            <button className="back" onClick={() => setPage('list')}>←</button>
            <div>
              <h1>校对知识点</h1>
              <p className="sub">确4认对了再出变式</p>
            </div>
          </div>
          <div className="scroll">
            <div className="card">
              <span className="badge">原题 {cur.id}</span>
              <div><MathText text={cur.stem} /></div>
              {cur.options?.map((o) => (
                <div key={o}>{o}</div>
              ))}
            </div>
            <div className="meta">
              <span>学科 <b>数学</b></span>
              <span>题型 <b>{tag.item_type}</b></span>
            </div>
            <p>AI 标注（可改）</p>
            <div className="chips">
              <button className="chip on">{labelOf(picked)}</button>
              {tag.candidates
                .filter((c) => c.knowledge_id !== picked)
                .map((c) => (
                  <button
                    key={c.knowledge_id}
                    className="chip"
                    onClick={() => setPicked(c.knowledge_id)}
                  >
                    {c.knowledge_label}
                  </button>
                ))}
              <button className="chip add" onClick={() => setPicker(true)}>
                + 添加知识点
              </button>
            </div>
            {err && <p className="sub">{err}</p>}
          </div>
          <div className="cta">
            <button className="primary" onClick={makeVariants}>
              确认，生成变式
            </button>
          </div>
        </>
      )}

      {page === 'var' && cur && (
        <>
          <div className="topbar">
            <button className="back" onClick={() => setPage('tag')}>←</button>
            <div>
              <h1>变式练习</h1>
              <p className="sub">{labelOf(picked)}</p>
            </div>
          </div>
          <div className="scroll">
            <div className="qty">
              题量
              <button onClick={() => setN((x) => Math.max(2, x - 1))}>−</button>
              <b>{n}</b>
              <button onClick={() => setN((x) => Math.min(5, x + 1))}>+</button>
            </div>
            <div className="card">
              <span className="badge">原题</span>
              <div><MathText text={cur.stem} /></div>
            </div>
            {kept.map((v, i) => (
              <div key={v.stem} className="card">
                <span className="badge">变式 {i + 1}</span>
                <div><MathText text={v.stem} /></div>
                <div className="pair">
                  <button
                    className={v.like ? 'primary' : 'ghost'}
                    onClick={() =>
                      setVariants((xs) =>
                        xs.map((x) => (x.stem === v.stem ? { ...x, like: true } : x)),
                      )
                    }
                  >
                    像原题
                  </button>
                  <button
                    className="ghost"
                    onClick={() =>
                      setVariants((xs) =>
                        xs.map((x) => (x.stem === v.stem ? { ...x, like: false } : x)),
                      )
                    }
                  >
                    不像
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="cta">
            <button className="ghost" onClick={makeVariants}>重新生成</button>
            <button className="primary" disabled={busy || kept.length === 0} onClick={() => sendCard(false)}>
              {busy ? '生成中' : '发给家长'}
            </button>
          </div>
          <p className="footnote">系统图片 / PDF，不建家长端
            {' · '}
            <button className="back" disabled={busy || kept.length === 0} onClick={() => sendCard(true)}>PDF</button>
          </p>
        </>
      )}

      {picker && tree && (
        <div className="picker" onClick={() => setPicker(false)}>
          <div className="sheet" onClick={(e) => e.stopPropagation()}>
            <h1>知识点树</h1>
            {tree.chapters.map((ch) => (
              <div key={ch.id}>
                <div className="ch">
                  {ch.term} {ch.label}
                </div>
                <div className="chips">
                  {ch.nodes.map((n) => (
                    <button
                      key={n.id}
                      className={picked === n.id ? 'chip on' : 'chip'}
                      onClick={() => {
                        setPicked(n.id)
                        setPicker(false)
                      }}
                    >
                      {n.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {page === 'var' && cur && (
        <div className="share-card" ref={cardRef}>
          <h2>练习卡</h2>
          <div className="kp">{labelOf(picked)}</div>
          <div className="block">
            <div className="lab">原题</div>
            <MathText text={cur.stem} />
            {cur.options?.map((o) => (
              <div key={o}>{o}</div>
            ))}
          </div>
          {kept.map((v, i) => (
            <div className="block" key={v.stem}>
              <div className="lab">变式 {i + 1}</div>
              <MathText text={v.stem} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
