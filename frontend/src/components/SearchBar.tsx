import { useState } from 'react'

const EXAMPLE_QUERY = "Find Nike Pegasus 41 men's size 10 black under $120"

interface Props {
  onSearch: (query: string) => void
  isLoading: boolean
}

export default function SearchBar({ onSearch, isLoading }: Props) {
  const [value, setValue] = useState('')

  function submit(query: string) {
    const trimmed = query.trim()
    if (trimmed) onSearch(trimmed)
  }

  return (
    <div className="w-full max-w-2xl">
      <form
        className="flex flex-col gap-3 sm:flex-row"
        onSubmit={(e) => {
          e.preventDefault()
          submit(value)
        }}
      >
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="What product are you looking for?"
          className="flex-1 rounded-xl border border-white/10 bg-white/5 px-5 py-4 text-lg text-white placeholder:text-slate-400 shadow-inner backdrop-blur focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-400/40"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="rounded-xl bg-gradient-to-r from-sky-500 to-indigo-500 px-6 py-4 text-lg font-semibold text-white shadow-lg shadow-sky-500/20 transition hover:from-sky-400 hover:to-indigo-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? 'Searching…' : 'Find Best Deal'}
        </button>
      </form>

      <button
        type="button"
        onClick={() => {
          setValue(EXAMPLE_QUERY)
          submit(EXAMPLE_QUERY)
        }}
        disabled={isLoading}
        className="mt-3 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-sm text-slate-300 transition hover:border-white/20 hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
      >
        Try: “{EXAMPLE_QUERY}”
      </button>
    </div>
  )
}

