import { useEffect, useMemo, useRef, useState } from 'react'
import { defaultWsUrl, EventSocket, type ConnectionState } from '../services/websocket'
import type { SecurityEvent } from '../types/event'

export function useWebSocket(paused: boolean) {
  const [state, setState] = useState<ConnectionState>('closed')
  const [events, setEvents] = useState<SecurityEvent[]>([])
  const pausedRef = useRef(paused)
  pausedRef.current = paused

  const client = useMemo(() => new EventSocket(defaultWsUrl()), [])

  useEffect(() => {
    const offState = client.onState(setState)
    const offMsg = client.onMessage((message) => {
      if (message.type !== 'security_event' || pausedRef.current) return
      const data = message.data as unknown as SecurityEvent
      setEvents((current) => [data, ...current].slice(0, 200))
    })
    client.connect()
    return () => {
      offState()
      offMsg()
      client.disconnect()
    }
  }, [client])

  return { state, events, setEvents }
}
