import { useEffect, useRef, useState } from 'react'
import { searchProducts } from '../api/client'
import Header from '../components/Header'
import LoadingStages from '../components/LoadingStages'
import ResultsList from '../components/ResultsList'
import SearchBar from '../components/SearchBar'
import type { SearchResponse } from '../types/product'

const STAGE_INTERVAL_MS = 700
const STAGE_COUNT = 4

export default function Home() {
  const [response, setResponse] = useState<SearchResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stage, setStage] = useState(0)
  const stageTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    return () => {
      if (stageTimer.current) clearInterval(stageTimer.current)
    }
  }, [])

  async function handleSearch(query: string) {
    setIsLoading(true)
    setError(null)
    setResponse(null)
    setStage(0)

    stageTimer.current = setInterval(() => {
      setStage((current) => Math.min(current + 1, STAGE_COUNT - 1))
    }, STAGE_INTERVAL_MS)

    try {
      const result = await searchProducts(query)
      setResponse(result)
    } catch {
      setError('Something went wrong reaching DealPilot. Is the backend running on port 8000?')
    } finally {
      if (stageTimer.current) clearInterval(stageTimer.current)
      setIsLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center gap-10 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 px-4 py-16">
      <Header />

      <SearchBar onSearch={handleSearch} isLoading={isLoading} />

      {isLoading && <LoadingStages activeStage={stage} />}

      {error && (
        <div className="flex w-full max-w-2xl animate-[fadeIn_0.3s_ease-out] items-start gap-3 rounded-xl border border-red-400/30 bg-red-500/10 px-5 py-4 text-red-200">
          <span aria-hidden="true" className="text-lg">⚠️</span>
          <p>{error}</p>
        </div>
      )}

      {!isLoading && response && <ResultsList response={response} />}
    </main>
  )
}

