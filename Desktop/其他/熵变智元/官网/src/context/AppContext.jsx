import React, { createContext, useContext, useMemo, useState, useEffect } from 'react'

const defaultLang = 'zh'

const AppContext = createContext(null)

export const AppProvider = ({ children }) => {
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || defaultLang)
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('auth_user')
    return raw ? JSON.parse(raw) : null
  })
  const [authModal, setAuthModal] = useState({ open: false, mode: 'login' })

  useEffect(() => {
    localStorage.setItem('lang', lang)
  }, [lang])

  useEffect(() => {
    if (user) localStorage.setItem('auth_user', JSON.stringify(user))
    else localStorage.removeItem('auth_user')
  }, [user])

  const value = useMemo(() => ({
    lang,
    setLang,
    user,
    setUser,
    authModal,
    setAuthModal
  }), [lang, user, authModal])

  return (
    <AppContext.Provider value={value}>{children}</AppContext.Provider>
  )
}

export const useApp = () => {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}

