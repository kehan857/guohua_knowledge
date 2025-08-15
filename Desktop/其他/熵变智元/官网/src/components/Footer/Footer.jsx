import React from 'react'
import { ArrowRight, Facebook, Twitter, Linkedin, Instagram, Mail, Phone, MapPin } from 'lucide-react'

const Footer = () => {
  const footerLinks = {
    product: [
      { name: "Features", href: "#features" },
      { name: "Pricing", href: "#pricing" },
      { name: "Templates", href: "#templates" },
      { name: "Integrations", href: "#integrations" }
    ],
    company: [
      { name: "About Us", href: "#about" },
      { name: "Careers", href: "#careers" },
      { name: "Press", href: "#press" },
      { name: "Contact", href: "#contact" }
    ],
    resources: [
      { name: "Blog", href: "#blog" },
      { name: "Help Center", href: "#help" },
      { name: "Community", href: "#community" },
      { name: "API Docs", href: "#api" }
    ],
    legal: [
      { name: "Privacy Policy", href: "#privacy" },
      { name: "Terms of Service", href: "#terms" },
      { name: "Cookie Policy", href: "#cookies" },
      { name: "GDPR", href: "#gdpr" }
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
              Write something
              <span className="block text-accent">good</span>
            </h2>
            <p className="text-lg text-gray-300 mb-8 max-w-2xl mx-auto">
              Join thousands of writers who trust YouMind to bring their ideas to life. 
              Start your free trial today.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-accent text-primary px-8 py-4 rounded-lg font-semibold hover:bg-yellow-400 transition-colors inline-flex items-center justify-center group">
                Start Free Trial
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              <button className="border border-white text-white px-8 py-4 rounded-lg font-semibold hover:bg-white hover:text-primary transition-colors">
                Contact Sales
              </button>
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
                <span className="text-2xl font-bold text-accent">YouMind</span>
              </div>
              <p className="text-gray-300 mb-6 leading-relaxed">
                Empowering writers worldwide with intelligent tools and seamless collaboration. 
                Transform your ideas into compelling content.
              </p>
              
              {/* Contact Info */}
              <div className="space-y-3 text-sm text-gray-300">
                <div className="flex items-center space-x-3">
                  <Mail className="w-4 h-4" />
                  <span>hello@youmind.com</span>
                </div>
                <div className="flex items-center space-x-3">
                  <Phone className="w-4 h-4" />
                  <span>+1 (555) 123-4567</span>
                </div>
                <div className="flex items-center space-x-3">
                  <MapPin className="w-4 h-4" />
                  <span>San Francisco, CA</span>
                </div>
              </div>
            </div>
            
            {/* Product Links */}
            <div>
              <h3 className="font-semibold text-white mb-4">Product</h3>
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
              <h3 className="font-semibold text-white mb-4">Company</h3>
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
              <h3 className="font-semibold text-white mb-4">Resources</h3>
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
              <h3 className="font-semibold text-white mb-4">Legal</h3>
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
            <div className="text-sm text-gray-400">
              © 2024 YouMind. All rights reserved.
            </div>
            
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