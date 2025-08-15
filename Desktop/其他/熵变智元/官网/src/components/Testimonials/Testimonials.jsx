import React, { useMemo } from 'react'
import { Star, Quote } from 'lucide-react'
import { translations } from '../../i18n/translations'
import { useApp } from '../../context/AppContext'

const Testimonials = () => {
  const { lang } = useApp()
  const t = useMemo(() => translations[lang], [lang])
  const testimonials = t.testimonials.items
  const stats = [
    { number: "10,000+", label: t.testimonials.stats.s1 },
    { number: "50M+", label: t.testimonials.stats.s2 },
    { number: "99%", label: t.testimonials.stats.s3 },
    { number: "24/7", label: t.testimonials.stats.s4 }
  ]

  return (
    <section id="testimonials" className="section-padding bg-white">
      <div className="container-max">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-primary mb-4">
            {t.testimonials.header1}
            <span className="block text-accent">{t.testimonials.header2}</span>
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">{t.testimonials.subtitle}</p>
        </div>
        
        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-16">
          {stats.map((stat, index) => (
            <div key={index} className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-primary mb-2">
                {stat.number}
              </div>
              <div className="text-gray-600 font-medium">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
        
        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          {testimonials.map((testimonial, index) => (
            <div key={index} className="card relative">
              {/* Quote Icon */}
              <div className="absolute top-4 right-4 text-accent/20">
                <Quote className="w-8 h-8" />
              </div>
              
              {/* Rating */}
              <div className="flex items-center space-x-1 mb-4">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-accent text-accent" />
                ))}
              </div>
              
              {/* Content */}
              <p className="text-gray-700 mb-6 leading-relaxed">
                "{testimonial.content}"
              </p>
              
              {/* Author */}
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 rounded-full bg-gray-200" />
                <div>
                  <div className="font-semibold text-primary">{testimonial.name}</div>
                  <div className="text-sm text-gray-600">{testimonial.role} · {testimonial.company}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Trust Indicators */}
        <div className="bg-muted rounded-2xl p-8">
          <div className="text-center mb-8">
            <h3 className="text-2xl font-bold text-primary mb-4">{t.testimonials.trustTitle}</h3>
            <p className="text-gray-600">{t.testimonials.trustDesc}</p>
          </div>
          
          {/* Company Logos Placeholder */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 items-center opacity-60">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-gray-300 h-12 rounded-lg flex items-center justify-center">
                <span className="text-gray-500 font-medium">Company {i}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

export default Testimonials