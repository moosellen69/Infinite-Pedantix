import { useState, useEffect, useMemo, useRef } from 'react'

interface Token {
  type: string
  content?: string
  length?: number
  is_revealed?: boolean
  hint?: string
  hint_color?: string
  revealed_word?: string
}

interface GuessHistoryItem {
  word: string
  occurrences: number
  color?: string
}

interface GameState {
  id: string
  tokens: Token[]
  title_tokens: Token[]
  revealed_words: string[]
  guess_history: GuessHistoryItem[]
  is_won: boolean
  is_gave_up: boolean
  title?: string
  wikipedia_url?: string
}

interface NewGameData {
  game_id: string
  tokens: Token[]
  title_tokens: Token[]
  total_words: number
}

interface GuessResponse {
  found: boolean
  occurrences: number
  hint_updates: any[]
  revealed_words: string[]
  guess_history: GuessHistoryItem[]
  is_won: boolean
  tokens?: Token[]
  title_tokens?: Token[]
}

function App() {
  const [game, setGame] = useState<GameState | null>(null)
  const [guess, setGuess] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const forestSeedRef = useRef(7)

  useEffect(() => {
    const PAL = {
      grass: '#8fc24a', grassLight: '#a4d25a', grassDark: '#6fa83c',
      grassShadow: '#5f9638', sandShadow: '#d2bf62',
      patch: '#b0da68', sand: '#f5e98a', sandEdge: '#e6d470',
      deep: '#24503a',
      trunk: '#7a5230', trunkOut: '#3a2618',
      white: '#f6f6ea', yellow: '#ffd84a', orange: '#f0902c', red: '#d8502c'
    }
    const LEAF = { out: '#1f3f2c', shade: '#3f7a34', base: '#5f9e3a', hi: '#8cc84a', spark: '#b6e06a' }
    const PINE = { out: '#16362e', shade: '#2a5e48', base: '#3b7a58', hi: '#5a9e6c' }
    const BUSH = { out: '#2a5a2c', shade: '#4c8e36', base: '#6cb040', hi: '#9cd058' }
    const ROCK = { out: '#1f2a36', shade: '#3d4a5c', base: '#5a6b7d', hi: '#8596a8' }

    const pack = (h: string) => {
      const n = parseInt(h.slice(1), 16)
      return ((255 << 24) | ((n & 255) << 16) | (n & 0xff00) | ((n >> 16) & 255)) >>> 0
    }

    const packPal = (p: Record<string, string>) => Object.fromEntries(Object.entries(p).map(([k, v]) => [k, pack(v)]))

    function mulberry32 (a: number) {
      return function () {
        a |= 0
        a = a + 0x6D2B79F5 | 0
        let t = Math.imul(a ^ a >>> 15, 1 | a)
        t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t
        return ((t ^ t >>> 14) >>> 0) / 4294967296
      }
    }

    function hash2 (x: number, y: number, s: number) {
      let h = Math.imul(x, 374761393) + Math.imul(y, 668265263) + Math.imul(s, 982451653)
      h = Math.imul(h ^ (h >>> 13), 1274126177)
      h ^= h >>> 16
      return (h >>> 0) / 4294967296
    }

    const drawForest = (canvas: HTMLCanvasElement, opts: { scale?: number; seed?: number; band?: number } = {}) => {
      const S = opts.scale || 4
      const seed = opts.seed ?? 7
      const band = opts.band ?? 0.2
      const W = Math.ceil(window.innerWidth / S)
      const H = Math.ceil(window.innerHeight / S)
      canvas.width = W
      canvas.height = H
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      const img = ctx.createImageData(W, H)
      const buf = new Uint32Array(img.data.buffer)
      const C = packPal(PAL), L = packPal(LEAF), P = packPal(PINE), B = packPal(BUSH), K = packPal(ROCK)
      const rand = mulberry32(seed)
      const R = (a: number, b: number) => a + rand() * (b - a)
      const inb = (x: number, y: number) => x >= 0 && y >= 0 && x < W && y < H
      const set = (x: number, y: number, c: number) => {
        x = Math.floor(x)
        y = Math.floor(y)
        if (inb(x, y)) buf[y * W + x] = c
      }
      const get = (x: number, y: number) => {
        x = Math.floor(x)
        y = Math.floor(y)
        return inb(x, y) ? buf[y * W + x] : 0
      }
      const bandY = (x: number) => H * band + Math.sin(x * 0.07 + seed) * 4 + Math.sin(x * 0.19) * 2

      buf.fill(C.grass)
      for (let y = 0; y < H; y++) {
        for (let x = 0; x < W; x++) {
          const n = hash2(x >> 1, y >> 1, seed)
          if (n < 0.035) buf[y * W + x] = C.grassLight
          else if (n > 0.975) buf[y * W + x] = C.grassDark
        }
      }

      function patch (cx: number, cy: number, rx: number, ry: number, col: number, edge?: number) {
        for (let y = Math.floor(cy - ry - 2); y <= cy + ry + 2; y++) {
          for (let x = Math.floor(cx - rx - 2); x <= cx + rx + 2; x++) {
            const dx = (x - cx) / rx
            const dy = (y - cy) / ry
            const d = dx * dx + dy * dy + (hash2(x >> 1, y >> 1, seed + 3) - 0.5) * 0.35
            if (d < 1) set(x, y, edge && d > 0.7 ? edge : col)
          }
        }
      }

      for (let i = 0; i < W * H / 4000; i++) patch(R(0, W), R(0, H), R(8, 20), R(4, 9), C.patch)
      for (let i = 0; i < Math.max(2, W * H / 30000); i++) {
        const cx = R(W * 0.15, W * 0.85)
        const cy = R(H * 0.3, H * 0.95)
        for (let j = 0; j < 3; j++) patch(cx + R(-8, 8), cy + R(-4, 4), R(6, 12), R(3, 6), C.sand, C.sandEdge)
      }

      for (let x = 0; x < W; x++) {
        const b = bandY(x) - 6
        for (let y = 0; y < b && y < H; y++) buf[y * W + x] = C.deep
      }

      const isGround = (c: number) => c === C.grass || c === C.grassLight || c === C.patch
      for (let i = 0; i < W * H / 90; i++) {
        const x = Math.floor(R(0, W))
        const y = Math.floor(R(0, H))
        if (!isGround(get(x, y))) continue
        set(x, y, C.grassDark)
        set(x + 1, y - 1, C.grassDark)
        set(x + 2, y, C.grassDark)
        set(x + 1, y, C.grassLight)
      }

      const objs: Array<{ t: string; x: number; y: number; r: number }> = []
      for (let gy = -4; gy < H * band + 12; gy += 6) {
        for (let gx = -8; gx < W + 8; gx += R(8, 12)) {
          const x = gx + R(-2, 2)
          const y = gy + R(-2, 2)
          if (y > bandY(x) + 2) continue
          objs.push({ t: rand() < 0.28 ? 'pine' : 'tree', x, y, r: R(6, 9) })
        }
      }
      const sideW = Math.max(10, W * 0.1)
      for (let gy = H * band + 6; gy < H + 24; gy += R(6, 8)) {
        const w = sideW * (0.5 + hash2(Math.floor(gy), 1, seed) * 0.8)
        for (let gx = -6; gx < w; gx += R(8, 11)) {
          if (rand() < 0.85) objs.push({ t: rand() < 0.3 ? 'pine' : 'tree', x: gx + R(-2, 2), y: gy, r: R(6, 8.5) })
          if (rand() < 0.85) objs.push({ t: rand() < 0.3 ? 'pine' : 'tree', x: W - gx + R(-2, 2), y: gy + R(-2, 2), r: R(6, 8.5) })
        }
      }
      for (let i = 0; i < W * H / 3500; i++) {
        const x = R(0, W)
        const y = R(bandY(0) + 8, H + 4)
        objs.push({ t: rand() < 0.75 ? 'bush' : 'rock', x, y, r: R(2.5, 4.5) })
      }

      const shade = (x: number, y: number) => {
        const c = get(x, y)
        if (!c || c === C.deep || c === C.grassShadow || c === C.sandShadow) return
        set(x, y, c === C.sand || c === C.sandEdge ? C.sandShadow : C.grassShadow)
      }

      for (const o of objs) {
        const rx = o.t === 'tree' ? o.r * 1.1 : o.t === 'pine' ? 6 : o.r * 1.2
        const ry = rx * 0.42
        const cx = o.x + rx * 0.35
        const cy = o.y + 1
        for (let y = Math.floor(cy - ry); y <= cy + ry; y++) {
          for (let x = Math.floor(cx - rx); x <= cx + rx; x++) {
            const dx = (x - cx) / rx
            const dy = (y - cy) / ry
            if (dx * dx + dy * dy < 1) shade(x, y)
          }
        }
      }

      for (let i = 0; i < W * H / 2500; i++) {
        const cx = R(0, W)
        const cy = R(0, H)
        const orange = rand() < 0.5
        for (let j = 0, n = 2 + Math.floor(R(0, 4)); j < n; j++) {
          const x = Math.floor(cx + R(-6, 6))
          const y = Math.floor(cy + R(-4, 4))
          if (y < bandY(x) + 2) continue
          const petal = orange ? C.orange : C.white
          set(x - 1, y, petal)
          set(x + 1, y, petal)
          set(x, y - 1, petal)
          set(x, y + 1, petal)
          set(x, y, orange ? C.red : C.yellow)
        }
      }

      function blob (cx: number, cy: number, r: number, p: Record<string, number>, sq = 1) {
        const ph = rand() * 6.28
        const r2 = Math.ceil(r + 1)
        for (let dy = -r2; dy <= r2; dy++) {
          for (let dx = -r2; dx <= r2; dx++) {
            const ey = dy / sq
            const d = Math.hypot(dx, ey)
            const rr = r * (1 + 0.09 * Math.sin(Math.atan2(ey, dx) * 5 + ph))
            if (d > rr) continue
            const x = Math.floor(cx + dx)
            const y = Math.floor(cy + dy)
            let c = 0
            if (d > rr - 1.1) c = p.out
            else {
              const l = (-dx * 0.55 - ey * 0.85) / r + (((x + y) & 1) ? 0.07 : -0.07)
              c = l > 0.42 ? p.hi : l < -0.3 ? p.shade : p.base
              if (c === p.base && hash2(x, y, seed + 9) < 0.06) c = p.hi
              if (p.spark && l > 0.62 && hash2(x, y, seed + 5) < 0.3) c = p.spark
            }
            set(x, y, c)
          }
        }
      }

      function trunk (x: number, y: number, h: number) {
        for (let t = -h; t <= 0; t++) {
          set(x - 2, y + t, C.trunkOut)
          set(x - 1, y + t, C.trunk)
          set(x, y + t, C.trunk)
          set(x + 1, y + t, C.trunkOut)
        }
        set(x - 1, y + 1, C.trunkOut)
        set(x, y + 1, C.trunkOut)
      }

      function tree (x: number, y: number, r: number) {
        trunk(x, y, 3)
        blob(x, y - 3 - r * 0.75, r, L)
        blob(x, y - 3 - r * 1.45, r * 0.75, L)
        blob(x, y - 3 - r * 1.95, r * 0.45, L)
      }

      function pineTree (x: number, y: number, r: number) {
        trunk(x, y, 2)
        const Ht = r * 2.6
        const tiers = 3
        for (let i = tiers - 1; i >= 0; i--) {
          const top = y - 2 - Ht + i * Ht * 0.27
          const th = Math.floor(Ht * 0.42)
          const hw = 2.5 + i * 1.8 * (r / 7)
          for (let row = 0; row <= th; row++) {
            const half = 0.5 + (row / th) * hw
            for (let dx = -Math.ceil(half); dx <= Math.ceil(half); dx++) {
              if (Math.abs(dx) > half) continue
              const px = x + dx
              const py = Math.floor(top + row)
              let c = 0
              if (Math.abs(dx) > half - 1 || row === th || row === 0) c = P.out
              else {
                const l = -dx / half + (((px + py) & 1) ? 0.12 : -0.12)
                c = l > 0.3 ? P.hi : l < -0.4 ? P.shade : P.base
              }
              set(px, py, c)
            }
          }
        }
      }

      objs.sort((a, b) => a.y - b.y)
      for (const o of objs) {
        const x = Math.floor(o.x)
        const y = Math.floor(o.y)
        if (o.t === 'tree') tree(x, y, o.r)
        else if (o.t === 'pine') pineTree(x, y, o.r)
        else if (o.t === 'bush') {
          blob(x - o.r * 0.5, y - o.r * 0.6, o.r, B, 0.8)
          blob(x + o.r * 0.6, y - o.r * 0.5, o.r * 0.8, B, 0.8)
        } else {
          blob(x, y - 1, o.r * 0.8, K, 0.7)
        }
      }

      ctx.putImageData(img, 0, 0)
    }

    const forestCanvas = document.createElement('canvas')
    const renderForest = () => {
      drawForest(forestCanvas, { scale: 4, seed: forestSeedRef.current, band: 0.2 })
      document.documentElement.style.backgroundImage = 'url(' + forestCanvas.toDataURL() + ')'
      document.documentElement.style.backgroundSize = 'cover'
      document.documentElement.style.backgroundRepeat = 'no-repeat'
      document.documentElement.style.backgroundAttachment = 'fixed'
      document.documentElement.style.backgroundPosition = 'center'
    }

    renderForest()
    let resizeTimer: number | undefined
    const onResize = () => {
      clearTimeout(resizeTimer)
      resizeTimer = window.setTimeout(renderForest, 150)
    }
    window.addEventListener('resize', onResize)

    return () => {
      window.removeEventListener('resize', onResize)
      document.documentElement.style.backgroundImage = ''
      document.documentElement.style.backgroundSize = ''
      document.documentElement.style.backgroundRepeat = ''
      document.documentElement.style.backgroundAttachment = ''
      document.documentElement.style.backgroundPosition = ''
    }
  }, [])

  const renderToken = (token: Token) => {
    if (token.type === 'word') {
      const baseWidth = Math.max(1.2, (token.length || 4) * 0.52)
      const width = Math.min(baseWidth, 6.2)
      const isHinted = !!token.hint && !token.is_revealed
      
      const hintClass = token.hint_color === 'near'
        ? 'hint-near'
        : token.hint_color === 'medium'
          ? 'hint-medium'
          : token.hint_color === 'far'
            ? 'hint-far'
            : ''

      if (token.is_revealed || game?.is_won || game?.is_gave_up) {
        return (
          <span
            key={Math.random()}
            className={`revealed-word ${token.hint_color ? `text-${token.hint_color}` : ''}`}
            style={{ minWidth: `${width}em`, marginInline: '2px' }}
          >
            {token.revealed_word || '█'.repeat(token.length || 4)}
          </span>
        )
      }

      return (
        <span
          key={Math.random()}
          className={`masked-word ${hintClass}`}
          style={{
            width: `${width}em`,
            minWidth: '1.2em'
          }}
        >
          {isHinted ? (
            <span>{token.hint}</span>
          ) : (
            <span style={{ opacity: 0 }}>_</span>
          )}
        </span>
      )
    }
    if (token.type === 'punctuation' || token.type === 'number') {
      return <span key={Math.random()} style={{ marginRight: '2px' }}>{token.content}</span>
    }
    if (token.type === 'space') {
      return token.content === '\n' ? <br key={Math.random()} /> : <span key={Math.random()} style={{ display: 'inline-block', width: '4px' }} />
    }
    return null
  }

  const startNewGame = async () => {
    setLoading(true)
    setError('')
    try {
      console.log('Starting new game...')
      const response = await fetch('/api/game/new', { method: 'POST' })
      console.log('Response status:', response.status)
      
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }
      
      const data: NewGameData = await response.json()
      console.log('Game data:', data)
      
      setGame({
        id: data.game_id,
        tokens: data.tokens,
        title_tokens: data.title_tokens,
        revealed_words: [],
        guess_history: [],
        is_won: false,
        is_gave_up: false
      })
    } catch (err) {
      console.error('Error starting game:', err)
      setError(err instanceof Error ? err.message : 'Failed to start new game')
    } finally {
      setLoading(false)
    }
  }

  const submitGuess = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!game || !guess.trim()) return

    setLoading(true)
    setError('')
    try {
      console.log('Submitting guess:', guess, 'for game:', game.id)
      const response = await fetch(`/api/game/${game.id}/guess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guess })
      })
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('Guess failed:', response.status, errorText)
        
        // If game not found (404), start a new game
        if (response.status === 404) {
          console.log('Game not found, starting new game')
          await startNewGame()
          return
        }
        
        throw new Error(`HTTP error! status: ${response.status}: ${errorText}`)
      }
      
      const data: GuessResponse = await response.json()
      console.log('Guess response:', data)
      console.log('Updated tokens:', data.tokens)
      
      setGame(prev => prev ? {
        ...prev,
        revealed_words: data.revealed_words,
        guess_history: data.guess_history,
        is_won: data.is_won,
        tokens: data.tokens || prev.tokens,
        title_tokens: data.title_tokens || prev.title_tokens
      } : null)
      
      setGuess('')
    } catch (err) {
      console.error('Guess error:', err)
      setError(err instanceof Error ? err.message : 'Failed to submit guess')
    } finally {
      setLoading(false)
    }
  }

  const giveUp = async () => {
    if (!game) return

    setLoading(true)
    try {
      const response = await fetch(`/api/game/${game.id}/giveup`, { method: 'POST' })
      const data: GameState = await response.json()
      setGame(data)
    } catch (err) {
      setError('Failed to give up')
    } finally {
      setLoading(false)
    }
  }

  const revealAll = async () => {
    if (!game) return

    setLoading(true)
    try {
      const response = await fetch(`/api/game/${game.id}/reveal`, { method: 'POST' })
      const data: GameState = await response.json()
      setGame(data)
    } catch (err) {
      setError('Failed to reveal article')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    startNewGame()
  }, [])

  const guessHistoryColorClass = (color?: string) => {
    switch (color) {
      case 'near':
        return 'bg-red-200 text-red-900'
      case 'medium':
        return 'bg-orange-200 text-orange-900'
      case 'far':
        return 'bg-blue-200 text-blue-900'
      default:
        return 'bg-gray-200 text-gray-600'
    }
  }

  const guessHistoryLegend = [
    { label: 'far', color: 'far' },
    { label: 'medium', color: 'medium' },
    { label: 'near', color: 'near' }
  ]

  const visibleGuessHistory = useMemo(() => {
    if (!game?.guess_history) return []
    const seen = new Set<string>()
    const result = []
    for (let i = game.guess_history.length - 1; i >= 0; i--) {
      const item = game.guess_history[i]
      const normalized = item.word.trim().toLowerCase()
      if (!seen.has(normalized)) {
        seen.add(normalized)
        result.push(item)
      }
    }
    return result
  }, [game?.guess_history])

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md">
          <h1 className="text-2xl font-bold mb-4 text-red-600">Error</h1>
          <p className="text-gray-700 mb-4">{error}</p>
          <button
            onClick={startNewGame}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!game) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-lg">
          <h1 className="text-3xl font-bold mb-4">Endless Pedantix</h1>
          <p>{loading ? 'Loading...' : 'Starting game...'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="forest-scene">
      <div className="forest-content max-w-6xl mx-auto p-4 md:p-8 relative z-10">
        {/* Titre principal */}
        <div className="text-center mb-8">
          <h1 className="title-cloud text-2xl md:text-4xl mb-4 pixel-shadow" style={{ color: 'var(--outline-dark)', textShadow: '2px 2px 0 var(--outline-dark)' }}>
            ENDLESS PEDANTIX
          </h1>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Zone principale */}
          <div className="flex-1">
            {/* Formulaire de saisie */}
            {!game.is_won && !game.is_gave_up && (
              <form onSubmit={submitGuess} className="mb-6">
                <div className="flex flex-col sm:flex-row gap-3">
                  <input
                    type="text"
                    value={guess}
                    onChange={(e) => setGuess(e.target.value)}
                    placeholder="Guess a word..."
                    className="flex-1 pixel-input no-radius"
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="pixel-button no-radius"
                  >
                    GUESS
                  </button>
                </div>
              </form>
            )}
            
            {/* Titre caché */}
            <div className="panel-parchment mb-6 no-radius">
              <div className="text-center" style={{ fontFamily: "'Press Start 2P', monospace", fontSize: '14px', letterSpacing: '1px' }}>
                {game.title_tokens.map(token => renderToken(token))}
              </div>
            </div>

            {/* Contenu article */}
            <div className="panel-parchment mb-6 no-radius article-text" style={{ minHeight: '200px' }}>
              {game.tokens.map(token => renderToken(token))}
            </div>

            {/* Messages de fin */}
            {game.is_won && (
              <div className="message-panel message-win no-radius mb-6">
                <p style={{ fontFamily: "'Press Start 2P', monospace", fontSize: '12px', marginBottom: '8px', color: 'var(--outline-dark)' }}>
                  ★ YOU WON! ★
                </p>
                <p style={{ fontSize: '14px', marginBottom: '8px' }}>
                  <strong>Article:</strong> {game.title}
                </p>
                {game.wikipedia_url && (
                  <a 
                    href={game.wikipedia_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="pixel-button text-white"
                    style={{ display: 'inline-block', marginTop: '8px', textDecoration: 'none', fontSize: '10px' }}
                  >
                    VIEW
                  </a>
                )}
                <button
                  onClick={revealAll}
                  className="pixel-button ml-2"
                  style={{ marginTop: '8px', marginLeft: '8px' }}
                >
                  REVEAL
                </button>
              </div>
            )}

            {game.is_gave_up && (
              <div className="message-panel message-lose no-radius mb-6">
                <p style={{ fontFamily: "'Press Start 2P', monospace", fontSize: '12px', marginBottom: '8px', color: 'var(--outline-dark)' }}>
                  GAME OVER
                </p>
                <p style={{ fontSize: '14px', marginBottom: '8px' }}>
                  <strong>Article:</strong> {game.title}
                </p>
                {game.wikipedia_url && (
                  <a 
                    href={game.wikipedia_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="pixel-button"
                    style={{ display: 'inline-block', marginTop: '8px', textDecoration: 'none', fontSize: '10px' }}
                  >
                    VIEW
                  </a>
                )}
              </div>
            )}

            {/* Boutons d'action */}
            <div className="flex flex-wrap gap-3 mt-6">
              {!game.is_won && !game.is_gave_up && (
                <>
                  <button
                    onClick={giveUp}
                    className="pixel-button danger"
                  >
                    GIVE UP
                  </button>
                  <button
                    onClick={startNewGame}
                    className="pixel-button success"
                  >
                    NEW GAME
                  </button>
                </>
              )}
              {(game.is_won || game.is_gave_up) && (
                <button
                  onClick={startNewGame}
                  className="pixel-button success"
                >
                  NEW GAME
                </button>
              )}
            </div>
          </div>

          {/* Sidebar - Historique */}
          <div className="w-full lg:w-80">
            <div className="guess-history-panel no-radius p-4">
              <h3 style={{ fontFamily: "'Press Start 2P', monospace", fontSize: '14px', marginBottom: '8px' }}>
                HISTORY
              </h3>
              <div className="mb-4 flex flex-wrap gap-2">
                {guessHistoryLegend.map(item => (
                  <span key={item.label} className={`hint-badge ${item.color}`}>
                    {item.label}
                  </span>
                ))}
              </div>
              <p style={{ fontSize: '12px', marginBottom: '8px', color: 'var(--outline-dark)' }}>
                <strong>Total:</strong> {visibleGuessHistory.length}
              </p>
              <div className="flex flex-col gap-1">
                {visibleGuessHistory.map((item, index) => (
                  <div 
                    key={`${item.word}-${index}`}
                    className={`guess-history-item ${guessHistoryColorClass(item.color)}`}
                  >
                    <div className="guess-item-word">{item.word}</div>
                    <div className="guess-item-count">{item.occurrences} occ.</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
