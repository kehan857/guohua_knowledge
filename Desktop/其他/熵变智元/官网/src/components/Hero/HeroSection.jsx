import React, { useMemo } from 'react'
import { ArrowRight, PenTool, Sparkles } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { translations } from '../../i18n/translations'

const HeroSection = () => {
  const { lang, setAuthModal } = useApp()
  const t = useMemo(() => translations[lang], [lang])
  return (
    <section id="hero" className="section-padding bg-gradient-to-br from-muted to-white relative overflow-hidden">
      <div className="container-max">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div className="text-center lg:text-left">
            <div className="mb-6">
              <span className="inline-flex items-center px-4 py-2 rounded-full bg-accent/10 text-accent font-medium text-sm mb-4">
                <Sparkles className="w-4 h-4 mr-2" />
                {t.hero.badge}
              </span>
            </div>
            
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-primary mb-6 leading-tight">
              {t.hero.title1}
              <span className="block text-accent">{t.hero.title2}</span>
            </h1>
            
            <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-2xl">
              {t.hero.subtitle}
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <button onClick={()=>setAuthModal({ open: true, mode: 'register' })} className="btn-primary inline-flex items-center justify-center group">
                {t.hero.ctaPrimary}
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              <button className="btn-secondary">
                {t.hero.ctaSecondary}
              </button>
            </div>
            
            <div className="mt-12 flex items-center justify-center lg:justify-start space-x-8">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary">{t.hero.stats1.value}</div>
                <div className="text-sm text-gray-600">{t.hero.stats1.label}</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-primary">{t.hero.stats2.value}</div>
                <div className="text-sm text-gray-600">{t.hero.stats2.label}</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-primary">{t.hero.stats3.value}</div>
                <div className="text-sm text-gray-600">{t.hero.stats3.label}</div>
              </div>
            </div>
          </div>
          
          {/* Right Content - Illustration */}
          <div className="relative">
            <div className="relative z-10">
              {/* Main Writing Interface Mockup */}
              <div className="bg-white rounded-2xl shadow-2xl p-6 transform rotate-3 hover:rotate-0 transition-transform duration-300">
                <div className="flex items-center space-x-2 mb-4">
                  <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                  <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                  <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                </div>
                <div className="space-y-3">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-full"></div>
                  <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                  <div className="h-8 bg-accent/20 rounded w-2/3"></div>
                  <div className="h-4 bg-gray-200 rounded w-full"></div>
                  <div className="h-4 bg-gray-200 rounded w-4/5"></div>
                </div>
              </div>
              
              {/* Floating Elements */}
              <div className="absolute -top-4 -right-4 bg-accent text-primary p-3 rounded-full shadow-lg animate-bounce">
                <PenTool className="w-6 h-6" />
              </div>
              
              <div className="absolute -bottom-4 -left-4 bg-primary text-white p-3 rounded-full shadow-lg">
                <Sparkles className="w-6 h-6" />
              </div>
            </div>
            
            {/* Background Decoration */}
            <div className="absolute inset-0 bg-gradient-to-r from-accent/10 to-primary/10 rounded-3xl transform -rotate-6 scale-105"></div>
          </div>
        </div>
      </div>
      
      {/* Background Decorations */}
      <div className="absolute top-20 left-10 w-20 h-20 bg-accent/10 rounded-full blur-xl"></div>
      <div className="absolute bottom-20 right-10 w-32 h-32 bg-primary/10 rounded-full blur-xl"></div>
    </section>
  )
}

export default HeroSection