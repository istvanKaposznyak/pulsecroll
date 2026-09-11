import React, { useEffect, useState } from 'react'
import { supabase } from './supabaseClient'
import { Calendar as CalendarIcon, MapPin, Search, Sparkles, X, ExternalLink, Navigation, Tag } from 'lucide-react'

export default function App() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [activeDateFilter, setActiveDateFilter] = useState('all')
  const [activeCategory, setActiveCategory] = useState('all')
  const [customDate, setCustomDate] = useState('')
  const [selectedEvent, setSelectedEvent] = useState(null)

  const categories = [
    { id: 'Színház', label: 'Színház' },
    { id: 'Koncert', label: 'Koncert' },
    { id: 'Fesztivál', label: 'Fesztivál' },
    { id: 'Gasztro', label: 'Gasztro' },
    { id: 'Vásár', label: 'Vásár' },
    { id: 'Családi', label: 'Családi' },
    { id: 'Sport', label: 'Sport' },
    { id: 'Kiállítás', label: 'Kiállítás' },
    { id: 'Előadás', label: 'Előadás & Stand-up' },
    { id: 'Buli', label: 'Buli & Éjszakai élet' },
  ]

  useEffect(() => {
    fetchEvents()
  }, [])

  async function fetchEvents() {
    setLoading(true)
    const { data, error } = await supabase
      .from('esemenyek')
      .select('*')
      .order('datum', { ascending: true })

    if (error) {
      console.error('Hiba az adatok lekérésekor:', error)
    } else {
      setEvents(data || [])
    }
    setLoading(false)
  }

  const getTodayISO = () => {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  const getTomorrowISO = () => {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    const year = tomorrow.getFullYear()
    const month = String(tomorrow.getMonth() + 1).padStart(2, '0')
    const day = String(tomorrow.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  const matchesDateFilter = (eventDatum) => {
    if (activeDateFilter === 'all') return true
    if (!eventDatum) return false

    const cleanDate = String(eventDatum).trim()

    if (activeDateFilter === 'today') return cleanDate === getTodayISO()
    if (activeDateFilter === 'tomorrow') return cleanDate === getTomorrowISO()

    if (activeDateFilter === 'weekend') {
      const now = new Date()
      const dayOfWeek = now.getDay()
      const distToSat = (6 - dayOfWeek + 7) % 7
      const sat = new Date(now)
      sat.setDate(sat.getDate() + distToSat)
      const sun = new Date(sat)
      sun.setDate(sun.getDate() + 1)

      const satISO = sat.toISOString().split('T')[0]
      const sunISO = sun.toISOString().split('T')[0]

      return cleanDate === satISO || cleanDate === sunISO
    }

    if (activeDateFilter === 'custom' && customDate) {
      return cleanDate === customDate
    }

    return true
  }

  const filteredEvents = events.filter(event => {
    const matchesSearch = 
      event.cim?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      event.helyszin?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      event.leiras?.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesDate = matchesDateFilter(event.datum)

    const matchesCat = activeCategory === 'all' || 
      (event.kategoria && event.kategoria.toLowerCase() === activeCategory.toLowerCase())

    return matchesSearch && matchesDate && matchesCat
  })

  const getMapQuery = (event) => {
    if (!event) return 'Debrecen'
    const venue = event.helyszin?.trim() || ''
    const title = event.cim?.trim() || ''

    if (venue && !venue.toLowerCase().includes('debrecen')) {
      return `${venue}, Debrecen`
    }
    return venue || `${title}, Debrecen`
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 md:p-12">
      <header className="max-w-6xl mx-auto mb-10 text-center">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent mb-3 flex items-center justify-center gap-3">
          PulseScroll Debrecen <Sparkles className="text-cyan-400 w-8 h-8" />
        </h1>
        <p className="text-slate-400 text-lg">Debreceni programok, fesztiválok és események egy helyen</p>
      </header>

      {/* Kereső, Dátum és Kategória Menük */}
      <div className="max-w-4xl mx-auto mb-10 space-y-5">
        
        {/* Keresőmező */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Keresés esemény, helyszín vagy leírás alapján..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-800/80 border border-slate-700/60 rounded-xl py-3 pl-12 pr-4 text-slate-100 placeholder-slate-400 focus:outline-none focus:border-cyan-500 transition-all shadow-lg"
          />
        </div>

        {/* 1. Dátumszűrő Sor */}
        <div className="flex flex-wrap items-center justify-center gap-2">
          {[
            { id: 'today', label: 'Ma' },
            { id: 'tomorrow', label: 'Holnap' },
            { id: 'weekend', label: 'Hétvégén' },
            { id: 'all', label: 'Összes Esemény' },
          ].map((filter) => (
            <button
              key={filter.id}
              onClick={() => { setActiveDateFilter(filter.id); setCustomDate(''); }}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                activeDateFilter === filter.id
                  ? 'bg-cyan-500 text-slate-950 font-semibold shadow-lg shadow-cyan-500/20'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {filter.label}
            </button>
          ))}

          <div className="flex items-center gap-2 bg-slate-800 border border-slate-700/60 rounded-xl px-3 py-1.5">
            <CalendarIcon className="w-4 h-4 text-cyan-400" />
            <input
              type="date"
              value={customDate}
              onChange={(e) => {
                setCustomDate(e.target.value)
                setActiveDateFilter('custom')
              }}
              className="bg-transparent text-slate-200 text-sm focus:outline-none [color-scheme:dark]"
            />
          </div>
        </div>

        {/* 2. Műfaji Kategória Sor */}
        <div className="flex flex-wrap items-center justify-center gap-2 pt-2 border-t border-slate-800/80">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(activeCategory === cat.id ? 'all' : cat.id)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeCategory === cat.id
                  ? 'bg-gradient-to-r from-blue-600 to-cyan-500 text-white shadow-md shadow-cyan-500/20'
                  : 'bg-slate-800/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-700/40'
              }`}
            >
              <Tag className="w-3 h-3 opacity-70" />
              {cat.label}
            </button>
          ))}
        </div>

      </div>

      {/* Esemény Csempék */}
      <main className="max-w-6xl mx-auto">
        {loading ? (
          <div className="text-center py-20 text-slate-400">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400 mb-4"></div>
            <p>Események betöltése...</p>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="text-center py-20 text-slate-400 bg-slate-800/30 rounded-2xl border border-slate-800">
            Nincs a kiválasztott szűrőknek megfelelő esemény a rendszerben.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredEvents.map((event) => (
              <div 
                key={event.id} 
                onClick={() => setSelectedEvent(event)}
                className="bg-slate-800/50 border border-slate-700/50 hover:border-cyan-500/50 rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-cyan-500/10 flex flex-col justify-between cursor-pointer group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="inline-flex items-center gap-1.5 bg-cyan-950/80 border border-cyan-500/30 text-cyan-300 text-xs font-semibold px-3 py-1 rounded-full">
                      <CalendarIcon className="w-3.5 h-3.5" />
                      <span>{event.datum}</span>
                    </div>

                    {event.kategoria && (
                      <span className="text-[11px] font-bold text-slate-400 bg-slate-700/50 border border-slate-600/40 px-2.5 py-0.5 rounded-md uppercase tracking-wider">
                        {event.kategoria}
                      </span>
                    )}
                  </div>

                  <h2 className="text-xl font-bold text-slate-100 mb-3 line-clamp-2 group-hover:text-cyan-400 transition-colors">
                    {event.cim}
                  </h2>

                  {event.leiras && (
                    <p className="text-slate-400 text-sm line-clamp-3 mb-6">
                      {event.leiras}
                    </p>
                  )}
                </div>

                <div className="pt-4 border-t border-slate-700/40 flex items-center justify-between text-xs text-slate-400">
                  <span className="text-slate-400 font-medium">Kattints a részletekért</span>
                  <span className="text-cyan-400 font-semibold group-hover:translate-x-1 transition-transform">Részletek &rarr;</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Részletek Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-2xl max-w-2xl w-full p-6 md:p-8 relative shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto">
            
            <button
              onClick={() => setSelectedEvent(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-100 bg-slate-700/50 p-2 rounded-xl transition-all z-10"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="pr-8">
              {selectedEvent.kategoria && (
                <span className="inline-block text-xs font-bold text-cyan-400 bg-cyan-950/80 border border-cyan-500/30 px-3 py-1 rounded-full mb-2 uppercase tracking-wider">
                  {selectedEvent.kategoria}
                </span>
              )}
              <h2 className="text-2xl md:text-3xl font-bold text-slate-100">
                {selectedEvent.cim}
              </h2>
            </div>

            {/* Dátum & Helyszín */}
            <div className="space-y-2.5 bg-slate-900/90 p-4.5 rounded-xl border border-slate-700/70">
              <div className="flex items-center gap-2.5 text-cyan-400 font-semibold text-sm">
                <CalendarIcon className="w-4 h-4 shrink-0" />
                <span><strong>Időpont:</strong> {selectedEvent.datum}</span>
              </div>
              <div className="flex items-start gap-2.5 text-slate-200 text-sm font-medium">
                <MapPin className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <span><strong>Helyszín:</strong> {selectedEvent.helyszin}</span>
              </div>
            </div>

            {/* AI Ajánló */}
            {selectedEvent.ajanlo && (
              <div className="bg-gradient-to-r from-cyan-950/70 via-slate-900 to-blue-950/70 border border-cyan-500/40 p-5 rounded-xl shadow-lg">
                <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm mb-2.5">
                  <Sparkles className="w-4 h-4" />
                  <span>PulseScroll AI Ajánló</span>
                </div>
                <p className="text-slate-200 text-sm leading-relaxed italic">
                  "{selectedEvent.ajanlo}"
                </p>
              </div>
            )}

            {/* Google Térkép */}
            <div>
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Navigation className="w-4 h-4 text-cyan-400" />
                Helyszín Térképen ({selectedEvent.helyszin})
              </h3>
              <div className="w-full h-64 rounded-xl overflow-hidden border border-slate-700 bg-slate-900 shadow-inner">
                <iframe
                  title="Esemény helyszíne"
                  width="100%"
                  height="100%"
                  frameBorder="0"
                  scrolling="no"
                  src={`https://maps.google.com/maps?q=${encodeURIComponent(getMapQuery(selectedEvent))}&t=&z=16&ie=UTF8&iwloc=&output=embed`}
                ></iframe>
              </div>
            </div>

            {/* Leírás */}
            {selectedEvent.leiras && (
              <div>
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Leírás</h3>
                <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-line">
                  {selectedEvent.leiras}
                </p>
              </div>
            )}

            {/* Akció gombok */}
            <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-slate-700/60">
              {selectedEvent.url && (
                <a
                  href={selectedEvent.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 inline-flex items-center justify-center gap-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold py-3.5 px-4 rounded-xl transition-all text-sm shadow-lg shadow-cyan-500/20"
                >
                  <ExternalLink className="w-4 h-4" />
                  Forrás Megtekintése
                </a>
              )}

              <a
                href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(getMapQuery(selectedEvent))}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-200 py-3.5 px-4 rounded-xl transition-all text-sm"
              >
                <Navigation className="w-4 h-4 text-cyan-400" />
                Útvonaltervezés Google Térképen
              </a>
            </div>

          </div>
        </div>
      )}
    </div>
  )
}