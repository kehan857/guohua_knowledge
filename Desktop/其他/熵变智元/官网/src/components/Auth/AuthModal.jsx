import React, { useMemo, useState } from 'react'
import { X } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { translations } from '../../i18n/translations'

const emailRegex = /.+@.+\..+/

const AuthModal = () => {
  const { authModal, setAuthModal, lang, setUser } = useApp()
  const t = useMemo(() => translations[lang], [lang])
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')

  if (!authModal.open) return null

  const onClose = () => setAuthModal({ open: false, mode: 'login' })

  const submit = (e) => {
    e.preventDefault()
    setError('')
    if (!emailRegex.test(email)) return setError(t.auth.invalidEmail)
    if (!password) return setError(t.auth.required)
    if (authModal.mode === 'register' && password !== confirmPassword) return setError(t.auth.passwordMismatch)

    const fakeUser = { id: Date.now(), email }
    setUser(fakeUser)
    onClose()
    alert(authModal.mode === 'login' ? t.auth.successLogin : t.auth.successRegister)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 relative">
        <button onClick={onClose} className="absolute right-4 top-4 text-gray-500 hover:text-primary">
          <X className="w-5 h-5" />
        </button>
        <h3 className="text-2xl font-bold text-primary mb-6">
          {authModal.mode === 'login' ? t.auth.login : t.auth.register}
        </h3>

        {error ? (
          <div className="mb-4 text-sm text-red-600">{error}</div>
        ) : null}

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">{t.auth.email}</label>
            <input value={email} onChange={(e)=>setEmail(e.target.value)} type="email" className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary focus:outline-none" placeholder="name@example.com"/>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">{t.auth.password}</label>
            <input value={password} onChange={(e)=>setPassword(e.target.value)} type="password" className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary focus:outline-none"/>
          </div>
          {authModal.mode === 'register' ? (
            <div>
              <label className="block text-sm text-gray-600 mb-1">{t.auth.confirmPassword}</label>
              <input value={confirmPassword} onChange={(e)=>setConfirmPassword(e.target.value)} type="password" className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary focus:outline-none"/>
            </div>
          ) : null}

          <button type="submit" className="btn-primary w-full">
            {authModal.mode === 'login' ? t.auth.loginNow : t.auth.registerNow}
          </button>
        </form>

        <div className="text-sm text-gray-600 mt-4 text-center">
          {authModal.mode === 'login' ? (
            <>
              {t.auth.noAccount}
              <button onClick={()=>setAuthModal({ open: true, mode: 'register' })} className="text-primary ml-2">{t.auth.register}</button>
            </>
          ) : (
            <>
              {t.auth.haveAccount}
              <button onClick={()=>setAuthModal({ open: true, mode: 'login' })} className="text-primary ml-2">{t.auth.login}</button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default AuthModal

