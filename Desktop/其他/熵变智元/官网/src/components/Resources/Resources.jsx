import React from 'react'
import { ArrowRight, BookOpen, Play, Download } from 'lucide-react'

const Resources = () => {
  const resources = [
    {
      type: "Guide",
      title: "The Complete Guide to Content Writing",
      description: "Master the art of creating compelling content that engages and converts your audience.",
      image: "https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20content%20writing%20guide%20book%20cover%20design%20clean%20professional%20blue%20theme&image_size=landscape_4_3",
      icon: <BookOpen className="w-5 h-5" />,
      readTime: "15 min read",
      category: "Writing Tips"
    },
    {
      type: "Video",
      title: "Getting Started with YouMind",
      description: "Watch this comprehensive tutorial to learn how to make the most of YouMind's features.",
      image: "https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=video%20tutorial%20thumbnail%20youmind%20interface%20modern%20clean%20design%20play%20button&image_size=landscape_4_3",
      icon: <Play className="w-5 h-5" />,
      readTime: "12 min watch",
      category: "Tutorial"
    },
    {
      type: "Template",
      title: "Blog Post Templates Pack",
      description: "Download our collection of proven blog post templates that drive engagement and traffic.",
      image: "https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=blog%20post%20template%20design%20layout%20modern%20typography%20clean%20professional&image_size=landscape_4_3",
      icon: <Download className="w-5 h-5" />,
      readTime: "Free download",
      category: "Templates"
    }
  ]

  const categories = [
    { name: "All", count: 24, active: true },
    { name: "Writing Tips", count: 8, active: false },
    { name: "Tutorials", count: 6, active: false },
    { name: "Templates", count: 10, active: false }
  ]

  return (
    <section id="resources" className="section-padding bg-muted">
      <div className="container-max">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-primary mb-4">
            Learn more about
            <span className="block text-accent">YouMind</span>
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Discover tips, tutorials, and resources to help you become a better writer 
            and make the most of YouMind's powerful features.
          </p>
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
                  <span className="text-sm">Read more</span>
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </article>
          ))}
        </div>
        
        {/* Newsletter Signup */}
        <div className="bg-white rounded-2xl p-8 shadow-lg">
          <div className="max-w-2xl mx-auto text-center">
            <h3 className="text-2xl font-bold text-primary mb-4">
              Stay updated with writing tips
            </h3>
            <p className="text-gray-600 mb-6">
              Get the latest writing tips, YouMind updates, and exclusive content 
              delivered straight to your inbox.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
              <input 
                type="email" 
                placeholder="Enter your email"
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
              <button className="btn-primary whitespace-nowrap">
                Subscribe
              </button>
            </div>
            
            <p className="text-xs text-gray-500 mt-4">
              No spam, unsubscribe at any time. Read our privacy policy.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Resources