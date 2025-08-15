import React from 'react'
import { Star, Quote } from 'lucide-react'

const Testimonials = () => {
  const testimonials = [
    {
      name: "Sarah Chen",
      role: "Content Creator",
      company: "TechBlog",
      avatar: "https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20headshot%20of%20asian%20woman%20content%20creator%20smiling%20modern%20clean%20background&image_size=square",
      content: "YouMind has completely transformed how I approach writing. The AI suggestions are incredibly helpful, and the collaborative features make working with my team seamless.",
      rating: 5
    },
    {
      name: "Marcus Johnson",
      role: "Author",
      company: "Bestselling Novelist",
      avatar: "https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20headshot%20of%20african%20american%20male%20author%20confident%20smile%20modern%20background&image_size=square",
      content: "As a novelist, I need tools that don't get in my way. YouMind's interface is so intuitive that I can focus entirely on my story. The research tools are a game-changer.",
      rating: 5
    },
    {
      name: "Emily Rodriguez",
      role: "Marketing Manager",
      company: "StartupCo",
      avatar: "https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20headshot%20of%20hispanic%20woman%20marketing%20manager%20friendly%20smile%20office%20background&image_size=square",
      content: "The templates and publishing features have streamlined our content creation process. We've increased our output by 300% while maintaining quality.",
      rating: 5
    },
    {
      name: "David Kim",
      role: "Technical Writer",
      company: "DevTools Inc",
      avatar: "https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20headshot%20of%20korean%20male%20technical%20writer%20glasses%20modern%20tech%20background&image_size=square",
      content: "The version control and collaboration features are exactly what our documentation team needed. YouMind understands the needs of technical writers.",
      rating: 5
    }
  ]

  const stats = [
    { number: "10,000+", label: "Happy Writers" },
    { number: "50M+", label: "Words Written" },
    { number: "99%", label: "Satisfaction Rate" },
    { number: "24/7", label: "Support" }
  ]

  return (
    <section id="testimonials" className="section-padding bg-white">
      <div className="container-max">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-primary mb-4">
            Our users love
            <span className="block text-accent">YouMind</span>
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Don't just take our word for it. Here's what writers around the world 
            are saying about their experience with YouMind.
          </p>
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
                <img 
                  src={testimonial.avatar} 
                  alt={testimonial.name}
                  className="w-12 h-12 rounded-full object-cover"
                />
                <div>
                  <div className="font-semibold text-primary">
                    {testimonial.name}
                  </div>
                  <div className="text-sm text-gray-600">
                    {testimonial.role} at {testimonial.company}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Trust Indicators */}
        <div className="bg-muted rounded-2xl p-8">
          <div className="text-center mb-8">
            <h3 className="text-2xl font-bold text-primary mb-4">
              Trusted by teams worldwide
            </h3>
            <p className="text-gray-600">
              From individual creators to enterprise teams, YouMind powers content creation across industries.
            </p>
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