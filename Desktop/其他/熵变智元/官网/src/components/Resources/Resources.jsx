import React, { useMemo } from 'react'
import { ArrowRight, BookOpen, Play, Download } from 'lucide-react'
import { translations } from '../../i18n/translations'
import { useApp } from '../../context/AppContext'

const Resources = () => {
  const { lang } = useApp()
  const t = useMemo(() => translations[lang], [lang])
  const resources = [
    { type: t.resources.list.guide.type, title: t.resources.list.guide.title, description: t.resources.list.guide.desc, image: "https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20content%20writing%20guide%20book%20cover%20design%20clean%20professional%20blue%20theme&image_size=landscape_4_3", icon: <BookOpen className="w-5 h-5" />, readTime: t.resources.list.guide.read, category: t.resources.list.guide.category },
    { type: t.resources.list.video.type, title: t.resources.list.video.title, description: t.resources.list.video.desc, image: "https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=video%20tutorial%20youmind%20interface%20modern%20clean%20design%20play%20button&image_size=landscape_4_3", icon: <Play className="w-5 h-5" />, readTime: t.resources.list.video.read, category: t.resources.list.video.category },
    { type: t.resources.list.template.type, title: t.resources.list.template.title, description: t.resources.list.template.desc, image: "https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=blog%20post%20template%20design%20layout%20modern%20typography%20clean%20professional&image_size=landscape_4_3", icon: <Download className="w-5 h-5" />, readTime: t.resources.list.template.read, category: t.resources.list.template.category }
  ]

  const categories = [
    { name: t.resources.categories.all, count: 24, active: true },
    { name: t.resources.categories.tips, count: 8, active: false },
    { name: t.resources.categories.tutorials, count: 6, active: false },
    { name: t.resources.categories.templates, count: 10, active: false }
  ]

  return (
    <section id="resources" className="section-padding bg-muted">
      <div className="container-max">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-primary mb-4">
            {t.resources.header1}
            <span className="block text-accent">{t.resources.header2}</span>
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">{t.resources.desc}</p>
        </div>
        
        {/* Category Filter */}
        <div className="flex flex-wrap justify-center gap-4 mb-12">
          {categories.map((category, index) => (
            <button
              key={index}
              className={`px-6 py-3 rounded-full font-medium transition-all duration-200 ${
                category.active
                  ? 'bg-primary text-white shadow-lg'
                  : 'bg-white text-gray-600 hover:bg-gray-50 border'
              }`}
            >
              {category.name}
              <span className="ml-2 text-sm opacity-75">({category.count})</span>
            </button>
          ))}
        </div>
        
        {/* Resources Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          {resources.map((resource, index) => (
            <article key={index} className="card group cursor-pointer">
              {/* Image */}
              <div className="relative overflow-hidden rounded-lg mb-6">
                <img 
                  src={resource.image} 
                  alt={resource.title}
                  className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
                />
                <div className="absolute top-4 left-4">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                    resource.type === 'Guide' ? 'bg-blue-100 text-blue-800' :
                    resource.type === 'Video' ? 'bg-red-100 text-red-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {resource.icon}
                    <span className="ml-2">{resource.type}</span>
                  </span>
                </div>
              </div>
              
              {/* Content */}
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-accent font-medium">{resource.category}</span>
                  <span className="text-gray-500">{resource.readTime}</span>
                </div>
                
                <h3 className="text-xl font-semibold text-primary group-hover:text-accent transition-colors">
                  {resource.title}
                </h3>
                
                <p className="text-gray-600 leading-relaxed">
                  {resource.description}
                </p>
                
                <div className="flex items-center text-primary font-medium group-hover:text-accent transition-colors">
                  <span className="text-sm">{t.resources.list.readmore}</span>
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </article>
          ))}
        </div>
        
        {/* Newsletter Signup */}
        <div className="bg-white rounded-2xl p-8 shadow-lg">
          <div className="max-w-2xl mx-auto text-center">
            <h3 className="text-2xl font-bold text-primary mb-4">{t.resources.list.newsletterTitle}</h3>
            <p className="text-gray-600 mb-6">{t.resources.list.newsletterDesc}</p>
            
            <div className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
              <input 
                type="email" 
                placeholder="Enter your email"
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
              <button className="btn-primary whitespace-nowrap">{t.resources.list.subscribe}</button>
            </div>
            
            <p className="text-xs text-gray-500 mt-4">{t.resources.list.privacy}</p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Resources