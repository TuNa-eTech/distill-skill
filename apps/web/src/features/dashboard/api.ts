import { useEffect, useState } from 'react'

type ApiState<T> = {
  data: T | null
  error: string | null
  loading: boolean
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

function buildApiUrl(path: string) {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  return `${API_BASE_URL}${path.startsWith('/api') ? path.slice(4) : path}`
}

export function buildApiPath(
  path: string,
  params: Record<string, string | number | null | undefined> = {},
) {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === '') {
      continue
    }
    search.set(key, String(value))
  }
  const query = search.toString()
  return query.length > 0 ? `${path}?${query}` : path
}

export function useApiData<T>(path: string | null) {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    error: null,
    loading: path !== null,
  })

  useEffect(() => {
    if (path === null) {
      setState({ data: null, error: null, loading: false })
      return
    }

    const requestPath = path
    const controller = new AbortController()
    setState({ data: null, error: null, loading: true })

    async function load() {
      try {
        const response = await fetch(buildApiUrl(requestPath), {
          headers: { Accept: 'application/json' },
          signal: controller.signal,
        })
        const payload = (await response.json()) as T & { error?: string }
        if (!response.ok) {
          throw new Error(payload.error || `Request failed with ${response.status}`)
        }
        setState({ data: payload, error: null, loading: false })
      } catch (error) {
        if (controller.signal.aborted) {
          return
        }
        setState({
          data: null,
          error: error instanceof Error ? error.message : 'Unknown API error',
          loading: false,
        })
      }
    }

    void load()
    return () => controller.abort()
  }, [path])

  return state
}
