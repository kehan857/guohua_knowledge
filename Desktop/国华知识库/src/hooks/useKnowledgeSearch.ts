import { useState, useEffect } from 'react';

// Types
export interface KnowledgeItem {
  id: number;
  title: string;
  excerpt: string;
  category: string;
  tags: string[];
  views: number;
  favorites: number;
  updatedAt: string;
  isFavorite?: boolean;
}

interface SearchFilters {
  query?: string;
  category?: string;
  tag?: string;
}

// Mock knowledge data
const MOCK_KNOWLEDGE_BASE: KnowledgeItem[] = [
  {
    id: 1,
    title: '企业级SaaS产品销售话术大全',
    excerpt: '针对不同行业客户的定制化销售话术，包含开场白、需求挖掘、产品介绍、异议处理等全流程话术模板。每个环节都提供了多种表达方式，帮助销售人员根据不同客户特点灵活调整。',
    category: '营销话术',
    tags: ['SaaS', '销售话术', '全流程'],
    views: 342,
    favorites: 87,
    updatedAt: '2023-10-18',
    isFavorite: true
  },
  {
    id: 2,
    title: '新产品发布会直播脚本',
    excerpt: '完整的产品发布会直播流程框架，包含开场、产品演示、功能亮点、互动问答、促销转化等环节的关键话术。附带时间控制建议和应急预案，确保直播顺利进行。',
    category: '直播脚本',
    tags: ['直播', '产品发布', '促销'],
    views: 289,
    favorites: 65,
    updatedAt: '2023-10-12'
  },
  {
    id: 3,
    title: '技术支持与售后服务指南',
    excerpt: '全面的售后服务流程和标准解答，包括产品安装、使用问题、故障排除等常见客户需求的处理方案，提升客户满意度和忠诚度。',
    category: '售后服务',
    tags: ['技术支持', 'FAQ', '客户服务'],
    views: 412,
    favorites: 93,
    updatedAt: '2023-10-08',
    isFavorite: true
  },
  {
    id: 4,
    title: '短视频营销内容创作指南',
    excerpt: '针对不同平台算法特点的短视频内容创作模板，包含产品展示、客户见证、使用教程等场景的脚本框架。提供镜头建议、时长分配和关键话术参考。',
    category: '视频文案',
    tags: ['短视频', '内容创作', '平台算法'],
    views: 256,
    favorites: 58,
    updatedAt: '2023-10-01'
  },
  {
    id: 5,
    title: '企业级产品功能与优势详解',
    excerpt: '详细介绍企业级解决方案的核心功能、技术架构和独特优势，帮助销售人员清晰传达产品价值主张，应对客户技术咨询和需求分析。',
    category: '产品介绍',
    tags: ['产品功能', '技术架构', '价值主张'],
    views: 317,
    favorites: 76,
    updatedAt: '2023-09-28'
  },
  {
    id: 6,
    title: '成功客户案例分析与实践',
    excerpt: '深入分析各行业标杆客户的成功案例，包括需求痛点、解决方案实施过程和业务成果。提供可复用的销售策略和客户沟通要点，增强说服力。',
    category: '案例分享',
    tags: ['客户案例', '行业解决方案', '最佳实践'],
    views: 278,
    favorites: 62,
    updatedAt: '2023-09-25'
  }
];

// Custom hook for knowledge search functionality
function useKnowledgeSearch(initialFilters: SearchFilters = {}) {
  const [filters, setFilters] = useState<SearchFilters>(initialFilters);
  const [results, setResults] = useState<KnowledgeItem[]>(MOCK_KNOWLEDGE_BASE);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [favorites, setFavorites] = useState<number[]>(
    MOCK_KNOWLEDGE_BASE.filter(item => item.isFavorite).map(item => item.id)
  );

  // Apply search filters
  useEffect(() => {
    if (!filters.query && !filters.category && !filters.tag) {
      setResults(MOCK_KNOWLEDGE_BASE);
      return;
    }

    setIsSearching(true);
    
    // Simulate API call delay
    setTimeout(() => {
      let filteredResults = [...MOCK_KNOWLEDGE_BASE];
      
      // Apply filters
      if (filters.query) {
        const queryLower = filters.query.toLowerCase();
        filteredResults = filteredResults.filter(
          item => 
            item.title.toLowerCase().includes(queryLower) || 
            item.excerpt.toLowerCase().includes(queryLower) ||
            item.tags.some(tag => tag.toLowerCase().includes(queryLower))
        );
      }
      
      if (filters.category) {
        filteredResults = filteredResults.filter(
          item => item.category.toLowerCase() === filters.category.toLowerCase()
        );
      }
      
      if (filters.tag) {
        filteredResults = filteredResults.filter(
          item => item.tags.some(tag => tag.toLowerCase() === filters.tag.toLowerCase())
        );
      }
      
      // Update favorites status
      filteredResults = filteredResults.map(item => ({
        ...item,
        isFavorite: favorites.includes(item.id)
      }));
      
      setResults(filteredResults);
      setIsSearching(false);
    }, 500);
  }, [filters, favorites]);

  // Update filters
  const updateFilters = (newFilters: SearchFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  // Reset all filters
  const resetFilters = () => {
    setFilters({});
  };

  // Toggle favorite status
  const toggleFavorite = (id: number) => {
    setFavorites(prev => 
      prev.includes(id)
        ? prev.filter(itemId => itemId !== id)
        : [...prev, id]
    );
  };

  return {
    results,
    isSearching,
    filters,
    updateFilters,
    resetFilters,
    toggleFavorite,
    favorites
  };
}

export default useKnowledgeSearch;