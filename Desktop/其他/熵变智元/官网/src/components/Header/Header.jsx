import React, { useMemo, useState } from 'react'
import { Menu, X } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { translations } from '../../i18n/translations'

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const { lang, setLang, user, setUser, setAuthModal } = useApp()
  const t = useMemo(() => translations[lang], [lang])

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen)
  }

  return (
    <header className="bg-white shadow-sm sticky top-0 z-50">
      <div className="container-max">
        <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
          {/* Logo */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-2xl font-bold text-primary">{t.brand.name}</span>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-8">
              <a href="#hero" className="text-gray-700 hover:text-primary px-3 py-2 text-sm font-medium transition-colors">
                {t.nav.home}
              </a>
              <a href="#features" className="text-gray-700 hover:text-primary px-3 py-2 text-sm font-medium transition-colors">
                {t.nav.features}
              </a>
              <a href="#testimonials" className="text-gray-700 hover:text-primary px-3 py-2 text-sm font-medium transition-colors">
                {t.nav.reviews}
              </a>
              <a href="#resources" className="text-gray-700 hover:text-primary px-3 py-2 text-sm font-medium transition-colors">
                {t.nav.resources}
              </a>
              <div className="ml-4">
                <button onClick={()=>setLang(lang==='zh'?'en':'zh')} className="text-gray-700 hover:text-primary px-3 py-2 text-sm font-medium border rounded-lg">
                  {lang==='zh'? t.lang.en : t.lang.zh}
                </button>
              </div>
            </div>
          </nav>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-3">
            {user ? (
              <>
                <span className="text-sm text-gray-600">{user.email}</span>
                <button onClick={()=>setUser(null)} className="btn-secondary">{t.auth.logout}</button>
              </>
            ) : (
              <>
                <button onClick={()=>setAuthModal({ open: true, mode: 'login' })} className="btn-secondary">{t.auth.login}</button>
                <button onClick={()=>setAuthModal({ open: true, mode: 'register' })} className="btn-primary">{t.auth.register}</button>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={toggleMenu}
              className="text-gray-700 hover:text-primary p-2"
            >
              {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-white border-t">
              <a href="#hero" className="text-gray-700 hover:text-primary block px-3 py-2 text-base font-medium">
                {t.nav.home}
              </a>
              <a href="#features" className="text-gray-700 hover:text-primary block px-3 py-2 text-base font-medium">
                {t.nav.features}
              </a>
              <a href="#testimonials" className="text-gray-700 hover:text-primary block px-3 py-2 text-base font-medium">
                {t.nav.reviews}
              </a>
              <a href="#resources" className="text-gray-700 hover:text-primary block px-3 py-2 text-base font-medium">
                {t.nav.resources}
              </a>
              <button onClick={()=>setLang(lang==='zh'?'en':'zh')} className="text-gray-700 hover:text-primary block px-3 py-2 text-base font-medium border rounded-lg">
                {lang==='zh'? t.lang.en : t.lang.zh}
              </button>
              <div className="px-3 py-2">
                {user ? (
                  <button onClick={()=>setUser(null)} className="btn-primary w-full">{t.auth.logout}</button>
                ) : (
                  <div className="grid grid-cols-2 gap-3">
                    <button onClick={()=>setAuthModal({ open: true, mode: 'login' })} className="btn-secondary w-full">{t.auth.login}</button>
                    <button onClick={()=>setAuthModal({ open: true, mode: 'register' })} className="btn-primary w-full">{t.auth.register}</button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}

export default Header