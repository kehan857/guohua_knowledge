import React, { useState } from 'react'
import { Menu, X } from 'lucide-react'

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

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
              <span className="text-2xl font-bold text-primary">YouMind</span>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-8">
              <a href="#hero" className="text-gray-700 hover:text-primary px-3 py-2 text-sm font-medium transition-colors">
                Home
              </a>
              <a href="#features" className="text-gray-700 hover:text-primary px-3 py-2 text-sm font-medium transition-colors">
                Features
              </a>
              <a href="#testimonials" className="text-gray-700 hover:text-primary px-3 py-2 text-sm font-medium transition-colors">
                Reviews
              </a>
              <a href="#resources" className="text-gray-700 hover:text-primary px-3 py-2 text-sm font-medium transition-colors">
                Resources
              </a>
            </div>
          </nav>

          {/* Desktop CTA */}
          <div className="hidden md:block">
            <button className="btn-primary">
              Get Started
            </button>
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
                Home
              </a>
              <a href="#features" className="text-gray-700 hover:text-primary block px-3 py-2 text-base font-medium">
                Features
              </a>
              <a href="#testimonials" className="text-gray-700 hover:text-primary block px-3 py-2 text-base font-medium">
                Reviews
              </a>
              <a href="#resources" className="text-gray-700 hover:text-primary block px-3 py-2 text-base font-medium">
                Resources
              </a>
              <div className="px-3 py-2">
                <button className="btn-primary w-full">
                  Get Started
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}

export default Header