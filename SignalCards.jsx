import { useEffect, useState } from 'react'

export const SignalCards = ({ filter, onSignalClick }) => {
  const [signals, setSignals] = useState([])

  useEffect(() => {
    const fetchSignals = async () => {
      try {
        const res = await fetch('https://v3k-backend-api.onrender.com/get-signals')
        const data = await res.json()
        setSignals(data)
      } catch (err) {
        console.error('Error fetching signals:', err)
      }
    }

    fetchSignals()

    // Optionally, auto-refresh every X seconds:
    const interval = setInterval(fetchSignals, 60000) // every 60s
    return () => clearInterval(interval)
  }, [])

  const filtered = filter === 'All' ? signals : signals.filter(sig => sig.type === filter)

  return (
    <div className="grid gap-4 p-4 sm:grid-cols-2 lg:grid-cols-3">
      {filtered.map((sig, idx) => (
        <div
          key={idx}
          onClick={() => onSignalClick(sig)}
          className="cursor-pointer rounded-2xl border p-4 shadow-md dark:bg-gray-800 bg-white hover:scale-105 transition"
        >
          <h2 className="text-xl font-bold">{sig.symbol}</h2>
          <p className="text-sm opacity-70">{sig.strategy}</p>
          <div className="mt-2 text-sm">
            <span className="font-semibold">Timeframe:</span> {sig.timeframe}
          </div>
          <div className="text-sm">
            <span className="font-semibold">Type:</span> {sig.type}
          </div>
          <div className="mt-2 font-semibold text-green-500">₹ {sig.price}</div>
          <div className="text-xs mt-1 text-yellow-300">Signal Strength: {sig.strength}%</div>
        </div>
      ))}
    </div>
  )
}
