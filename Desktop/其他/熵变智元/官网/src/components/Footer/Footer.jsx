import React, { useMemo } from 'react'
import { ArrowRight, Facebook, Twitter, Linkedin, Instagram, Mail, Phone, MapPin } from 'lucide-react'
import { translations } from '../../i18n/translations'
import { useApp } from '../../context/AppContext'

const Footer = () => {
  const { lang } = useApp()
  const t = useMemo(() => translations[lang], [lang])
  const footerLinks = {
    product: [
      { name: t.footer.links.features, href: "#features" },
      { name: t.footer.links.pricing, href: "#pricing" },
      { name: t.footer.links.templates, href: "#templates" },
      { name: t.footer.links.integrations, href: "#integrations" }
    ],
    company: [
      { name: t.footer.links.about, href: "#about" },
      { name: t.footer.links.careers, href: "#careers" },
      { name: t.footer.links.press, href: "#press" },
      { name: t.footer.links.contact, href: "#contact" }
    ],
    resources: [
      { name: t.footer.links.blog, href: "#blog" },
      { name: t.footer.links.help, href: "#help" },
      { name: t.footer.links.community, href: "#community" },
      { name: t.footer.links.api, href: "#api" }
    ],
    legal: [
      { name: t.footer.links.privacy, href: "#privacy" },
      { name: t.footer.links.terms, href: "#terms" },
      { name: t.footer.links.cookies, href: "#cookies" },
      { name: t.footer.links.gdpr, href: "#gdpr" }
    ]
  }

  const socialLinks = [
    { icon: <Facebook className="w-5 h-5" />, href: "#", name: "Facebook" },
    { icon: <Twitter className="w-5 h-5" />, href: "#", name: "Twitter" },
    { icon: <Linkedin className="w-5 h-5" />, href: "#", name: "LinkedIn" },
    { icon: <Instagram className="w-5 h-5" />, href: "#", name: "Instagram" }
  ]

  return (
    <footer className="bg-primary text-white">
      {/* Main CTA Section */}
      <div className="bg-gradient-to-r from-primary to-secondary">
        <div className="container-max section-padding">
          <div className="text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              {t.footer.topTitle1}
              <span className="block text-accent">{t.footer.topTitle2}</span>
            </h2>
            <p className="text-lg text-gray-300 mb-8 max-w-2xl mx-auto">{t.footer.topDesc}</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-accent text-primary px-8 py-4 rounded-lg font-semibold hover:bg-yellow-400 transition-colors inline-flex items-center justify-center group">
                {t.footer.topPrimary}
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              <button className="border border-white text-white px-8 py-4 rounded-lg font-semibold hover:bg-white hover:text-primary transition-colors">{t.footer.topSecondary}</button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Footer Links */}
      <div className="container-max">
        <div className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-8">
            {/* Company Info */}
            <div className="lg:col-span-2">
              <div className="mb-6">
                <span className="text-2xl font-bold text-accent">{t.brand.name}</span>
              </div>
              <p className="text-gray-300 mb-6 leading-relaxed">{t.hero.subtitle}</p>
              
              {/* Contact Info */}
              <div className="space-y-3 text-sm text-gray-300">
                <div className="flex items-center space-x-3"><Mail className="w-4 h-4" /><span>{t.footer.contact.email}</span></div>
                <div className="flex items-center space-x-3"><Phone className="w-4 h-4" /><span>{t.footer.contact.phone}</span></div>
                <div className="flex items-center space-x-3"><MapPin className="w-4 h-4" /><span>{t.footer.contact.address}</span></div>
              </div>
            </div>
            
            {/* Product Links */}
            <div>
              <h3 className="font-semibold text-white mb-4">{t.footer.product}</h3>
              <ul className="space-y-3">
                {footerLinks.product.map((link, index) => (
                  <li key={index}>
                    <a href={link.href} className="text-gray-300 hover:text-accent transition-colors text-sm">
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
            
            {/* Company Links */}
            <div>
              <h3 className="font-semibold text-white mb-4">{t.footer.company}</h3>
              <ul className="space-y-3">
                {footerLinks.company.map((link, index) => (
                  <li key={index}>
                    <a href={link.href} className="text-gray-300 hover:text-accent transition-colors text-sm">
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
            
            {/* Resources Links */}
            <div>
              <h3 className="font-semibold text-white mb-4">{t.footer.resources}</h3>
              <ul className="space-y-3">
                {footerLinks.resources.map((link, index) => (
                  <li key={index}>
                    <a href={link.href} className="text-gray-300 hover:text-accent transition-colors text-sm">
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
            
            {/* Legal Links */}
            <div>
              <h3 className="font-semibold text-white mb-4">{t.footer.legal}</h3>
              <ul className="space-y-3">
                {footerLinks.legal.map((link, index) => (
                  <li key={index}>
                    <a href={link.href} className="text-gray-300 hover:text-accent transition-colors text-sm">
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
        
        {/* Bottom Bar */}
        <div className="border-t border-gray-700 py-8 px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            {/* Copyright */}
            <div className="text-sm text-gray-400">{t.footer.copyright}</div>
            
            {/* Social Links */}
            <div className="flex items-center space-x-4">
              {socialLinks.map((social, index) => (
                <a
                  key={index}
                  href={social.href}
                  className="text-gray-400 hover:text-accent transition-colors p-2 hover:bg-gray-700 rounded-lg"
                  aria-label={social.name}
                >
                  {social.icon}
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer