export type ConnectionState = 'connecting' | 'open' | 'closed' | 'error'

export interface WsMessage {
  type: string
  data?: Record<string, unknown>
}

type Listener = (message: WsMessage) => void
type StateListener = (state: ConnectionState) => void

export class EventSocket {
  private socket: WebSocket | null = null
  private listeners = new Set<Listener>()
  private stateListeners = new Set<StateListener>()
  private timer: number | null = null
  private closedByUser = false
  private attempt = 0

  constructor(private url: string) {}

  connect() {
    this.closedByUser = false
    this.open()
  }

  disconnect() {
    this.closedByUser = true
    if (this.timer) window.clearTimeout(this.timer)
    this.socket?.close()
    this.socket = null
    this.emitState('closed')
  }

  onMessage(listener: Listener) {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  onState(listener: StateListener) {
    this.stateListeners.add(listener)
    return () => this.stateListeners.delete(listener)
  }

  private open() {
    this.emitState('connecting')
    const socket = new WebSocket(this.url)
    this.socket = socket
    socket.onopen = () => {
      this.attempt = 0
      this.emitState('open')
    }
    socket.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as WsMessage
        this.listeners.forEach((listener) => listener(parsed))
      } catch {
        /* ignore malformed frames */
      }
    }
    socket.onerror = () => this.emitState('error')
    socket.onclose = () => {
      this.emitState('closed')
      if (!this.closedByUser) this.scheduleReconnect()
    }
  }

  private scheduleReconnect() {
    this.attempt += 1
    const delay = Math.min(15000, 500 * 2 ** this.attempt)
    this.timer = window.setTimeout(() => this.open(), delay)
  }

  private emitState(state: ConnectionState) {
    this.stateListeners.forEach((listener) => listener(state))
  }
}

export function defaultWsUrl() {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/ws/events`
}
