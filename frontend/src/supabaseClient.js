import { createClient } from '@supabase/supabase-js'

// Beolvassa a Vercel/Vite környezeti változókat, ha hiányoznak, a tartalék (fallback) értékeket használja
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://lhoozpsyhwmoqtmgxipe.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'sb_publishable_Lcr2K7MMYwYFnj27Ocoogw_lGjaCrmX'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)