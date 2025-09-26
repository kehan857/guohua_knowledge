import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
  import { 
  Bell, BookOpen, FileText, Video, Mic, Bookmark, 
  Settings, HelpCircle, Star, Menu, X, User, LogOut, Clock, MoreHorizontal
} from 'lucide-react';
import { toast } from 'sonner';

// Component imports
  import KnowledgeCard from '@/components/knowledge/KnowledgeCard';
import MarketingScriptGenerator from '@/components/knowledge/MarketingScriptGenerator';

// Hooks
import useKnowledgeSearch, { KnowledgeItem } from '@/hooks/useKnowledgeSearch';
import useLocalStorage from '@/hooks/useLocalStorage';

// Mock data for knowledge base
const KNOWLEDGE_CATEGORIES = [
  { id: 1, name: '营销话术', icon: <FileText size={18} />, description: '针对不同产品和场景的销售沟通话术模板，帮助快速打动客户' },
  { id: 2, name: '直播脚本', icon: <Mic size={18} />, description: '完整的直播流程框架和关键话术提示，提升直播转化效果' },
  { id: 3, name: '视频文案', icon: <Video size={18} />, description: '分产品、场景和风格的视频内容创作模板，提高内容质量' },
  { id: 4, name: '产品介绍', icon: <BookOpen size={18} />, description: '详细的产品功能、优势和价值主张介绍，帮助客户全面了解产品' },
  { id: 5, name: '售后服务', icon: <HelpCircle size={18} />, description: '客户使用过程中的常见问题解答和技术支持指南' },
  { id: 6, name: '案例分享', icon: <Star size={18} />, description: '成功客户案例分析和最佳实践分享，增强销售说服力' },
];

const POPULAR_TAGS = [
  { id: 1, name: '新产品', count: 24 },
  { id: 2, name: '促销活动', count: 18 },
  { id: 3, name: '客户异议', count: 32 },
  { id: 4, name: '竞品分析', count: 15 },
  { id: 5, name: '销售技巧', count: 27 },
];

// Quick access button component
const QuickAccessButton = ({ icon, label, colorClass, onClick }) => (
  <button 
    className={`flex flex-col items-center justify-center p-3 rounded-xl ${colorClass} text-white w-full transition-transform hover:scale-105`}
    onClick={onClick}
  >
    {icon}
    <span className="text-xs font-medium">{label}</span>
  </button>
);

export default function Home() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeCategory, setActiveCategory] = useState('all');
  const [activeTag, setActiveTag] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isScrolled, setIsScrolled] = useState(false);
  const [userRole] = useLocalStorage('userRole', 'sales'); // 'sales' or 'admin'
  
  const { 
    results, 
    isSearching, 
    updateFilters, 
    toggleFavorite 
  } = useKnowledgeSearch();

  // Handle scroll events for navbar styling
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Update search filters when query, category, or tag changes
  useEffect(() => {
    updateFilters({
      query: searchQuery,
      category: activeCategory !== 'all' ? activeCategory : undefined,
      tag: activeTag || undefined
    });
  }, [searchQuery, activeCategory, activeTag, updateFilters]);

  // Handle search input change
  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  // Handle category selection
  const handleCategorySelect = (category: string) => {
    setActiveCategory(category);
    setActiveTag('');
    // Scroll to results section on mobile
    if (window.innerWidth < 768) {
      document.getElementById('knowledge-results')?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Handle tag selection
  const handleTagSelect = (tag: string) => {
    setActiveTag(tag);
    // Scroll to results section on mobile
    if (window.innerWidth < 768) {
      document.getElementById('knowledge-results')?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Handle quick access button clicks
  const handleQuickAccess = (tool: string) => {
    toast.info(`正在打开${tool}...`);
    // In a real application, this would navigate to or open the selected tool
    if (tool === '营销话术生成器') {
      document.getElementById('script-generator')?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Render category pills
   const renderCategoryPills = () => null;

  // Render popular tags
  const renderPopularTags = () => null;

  // Render knowledge results
  const renderKnowledgeResults = () => {
    if (isSearching) {
      return (
        <div className="flex flex-col items-center justify-center py-16">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
          <p className="text-gray-500">正在搜索知识库内容...</p>
        </div>
      );
    }

    if (results.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <BookOpen size={48} className="text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">未找到相关内容</h3>
          <p className="text-gray-500 max-w-md">
            尝试使用不同的关键词、分类或标签进行搜索，或浏览推荐内容
          </p>
          <button
            onClick={() => {
              setSearchQuery('');
              setActiveCategory('all');
              setActiveTag('');
            }}
            className="mt-4 text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            查看全部内容
          </button>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {results.map((item) => (
          <KnowledgeCard
            key={item.id}
            item={item}
            onFavoriteToggle={toggleFavorite}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
       {/* Header/Navigation */}
      <header 
        className={`sticky top-0 z-50 w-full transition-all duration-300 ${
          isScrolled 
            ? 'bg-white shadow-sm py-2' 
            : 'bg-transparent py-4'
        }`}
      >
        <div className="container mx-auto px-4">
            <div className="flex items-center justify-between w-full">
            {/* Logo and brand */}
            <div className="flex items-center">
              <button 
                className="md:hidden mr-3"
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              >
                {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
              <div className="flex items-center">
                <BookOpen size={28} className="text-blue-600 mr-2" />
                  <h1 className="text-xl font-bold text-gray-900">国华生物慢病管理知识库</h1>
              </div>
            </div>

            {/* Desktop Navigation */}
              <nav className="hidden md:flex items-center space-x-0">
               <button className="px-6 py-2 rounded-lg text-sm font-medium text-blue-600 bg-blue-50">
                知识库
              </button>
              <button className="px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors">
                历史记录
              </button>
              {userRole === 'admin' && (
               <button className="px-6 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors">
                  管理中心
                </button>
              )}
            </nav>



            {/* User menu and actions */}
            <div className="flex items-center space-x-1">
              <button className="p-2 rounded-full text-gray-500 hover:bg-gray-100 relative">
                <Bell size={20} />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              
              <div className="relative group">
                <button className="flex items-center space-x-1 p-1 rounded-full hover:bg-gray-100">
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                    <User size={18} className="text-gray-600" />
                  </div>
                </button>
                
                {/* User dropdown menu */}
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 z-50 hidden group-hover:block">
                  <div className="px-4 py-2 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">销售代表</p>
                    <p className="text-xs text-gray-500">sales@example.com</p>
                  </div>
                  <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center">
                    <User size={16} className="mr-2 text-gray-500" />
                    个人资料
                  </button>
                  <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center">
                    <Settings size={16} className="mr-2 text-gray-500" />
                    设置
                  </button>
                  <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center">
                    <HelpCircle size={16} className="mr-2 text-gray-500" />
                    帮助中心
                  </button>
                  <button className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100 flex items-center">
                    <LogOut size={16} className="mr-2" />
                    退出登录
                  </button>
                </div>
              </div>
            </div>
          </div>


        </div>
      </header>

      {/* Right Side Floating Toolbar */}
      <div className="fixed right-4 top-1/3 z-40 hidden md:flex flex-col space-y-3">
        <button className="w-12 h-12 rounded-full bg-white shadow-lg flex items-center justify-center text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-all duration-300">
          <FileText size={20} />
        </button>
        <button className="w-12 h-12 rounded-full bg-white shadow-lg flex items-center justify-center text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-all duration-300">
          <Video size={20} />
        </button>
        <button className="w-12 h-12 rounded-full bg-white shadow-lg flex items-center justify-center text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-all duration-300">
          <Mic size={20} />
        </button>
        <button className="w-12 h-12 rounded-full bg-white shadow-lg flex items-center justify-center text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-all duration-300">
          <HelpCircle size={20} />
        </button>
        <button className="w-12 h-12 rounded-full bg-blue-600 shadow-lg flex items-center justify-center text-white hover:bg-blue-700 transition-all duration-300">
          <Settings size={20} />
        </button>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden absolute top-16 left-0 right-0 bg-white shadow-md z-40">
          <div className="px-4 py-3 space-y-1">
            <button className="w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-blue-600 bg-blue-50">
              知识库
            </button>

            <button className="w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100">
              收藏夹
            </button>
            {userRole === 'admin' && (
              <button className="w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100">
                管理中心
              </button>
            )}
            <div className="pt-2 border-t border-gray-100">
              <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center">
                <User size={16} className="mr-2 text-gray-500" />
                个人资料
              </button>
              <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center">
                <Settings size={16} className="mr-2 text-gray-500" />
                设置
              </button>
              <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center">
                <HelpCircle size={16} className="mr-2 text-gray-500" />
                帮助中心
              </button>
              <button className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100 flex items-center">
                <LogOut size={16} className="mr-2" />
                退出登录
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-grow container mx-auto px-4 py-6">
        {/* Hero section with quick access tools */}
         <section className="mb-8">
           <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-2xl p-8 text-white shadow-lg w-full">
             <div className="container mx-auto text-center">
               <h2 className="text-3xl md:text-4xl font-bold mb-4">国华生物慢病管理知识库</h2>
              <p className="text-blue-100 mb-8 text-lg">
                专业的慢病管理知识平台，助力医疗健康事业发展
              </p>
              
                {/* Portal access panels with 3D floating effect */}
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
                  <div className="flex flex-col items-center justify-center p-5 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 shadow-lg shadow-blue-500/20 text-white w-full transition-all duration-300 hover:translate-y-[-8px] hover:shadow-xl hover:shadow-blue-500/30 transform hover:scale-105">
                    <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mb-3">
                      <FileText size={28} className="text-blue-100" />
                    </div>
                    <span className="text-sm font-medium">营销话术</span>
                  </div>
                  <div className="flex flex-col items-center justify-center p-5 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 shadow-lg shadow-blue-500/20 text-white w-full transition-all duration-300 hover:translate-y-[-8px] hover:shadow-xl hover:shadow-blue-500/30 transform hover:scale-105">
                    <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mb-3">
                      <Mic size={28} className="text-blue-100" />
                    </div>
                    <span className="text-sm font-medium">直播脚本</span>
                  </div>
                  <div className="flex flex-col items-center justify-center p-5 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 shadow-lg shadow-blue-500/20 text-white w-full transition-all duration-300 hover:translate-y-[-8px] hover:shadow-xl hover:shadow-blue-500/30 transform hover:scale-105">
                    <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mb-3">
                      <Video size={28} className="text-blue-100" />
                    </div>
                    <span className="text-sm font-medium">视频文案</span>
                  </div>
                  <div className="flex flex-col items-center justify-center p-5 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 shadow-lg shadow-blue-500/20 text-white w-full transition-all duration-300 hover:translate-y-[-8px] hover:shadow-xl hover:shadow-blue-500/30 transform hover:scale-105">
                    <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mb-3">
                      <BookOpen size={28} className="text-blue-100" />
                    </div>
                    <span className="text-sm font-medium">产品介绍</span>
                  </div>
                  <div className="flex flex-col items-center justify-center p-5 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 shadow-lg shadow-blue-500/20 text-white w-full transition-all duration-300 hover:translate-y-[-8px] hover:shadow-xl hover:shadow-blue-500/30 transform hover:scale-105">
                    <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mb-3">
                      <HelpCircle size={28} className="text-blue-100" />
                    </div>
                    <span className="text-sm font-medium">售后服务</span>
                  </div>
                  <div className="flex flex-col items-center justify-center p-5 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 shadow-lg shadow-blue-500/20 text-white w-full transition-all duration-300 hover:translate-y-[-8px] hover:shadow-xl hover:shadow-blue-500/30 transform hover:scale-105">
                    <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mb-3">
                      <Star size={28} className="text-blue-100" />
                    </div>
                    <span className="text-sm font-medium">案例分享</span>
                  </div>
                </div>
            </div>
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">


          {/* Main content area */}
            <div className="lg:col-span-4 space-y-8 bg-gray-50 -mx-4 px-4 py-6 rounded-t-3xl">
            {/* Mobile filters */}
            <div className="lg:hidden">
               {userRole === 'admin' && (
                <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-100 mb-6">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">管理功能</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <button className="flex items-center justify-center gap-2 text-sm font-medium text-gray-700 hover:bg-gray-100 p-2 rounded-lg transition-colors">
                      <Settings size={16} />
                      内容管理
                    </button>
                    <button className="flex items-center justify-center gap-2 text-sm font-medium text-gray-700 hover:bg-gray-100 p-2 rounded-lg transition-colors">
                      <FileText size={16} />
                      产品配置
                    </button>
                  </div>
                </div>
              )}
            </div>



             {/* Marketing Script Generator Tool */}
             <section id="script-generator" className="mb-8">
               <MarketingScriptGenerator className="w-full" />
             </section>

            {/* Knowledge results section */}
            <section id="knowledge-results">
               <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">AI知识智能体矩阵</h2>
               </div>
               
               <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                 {KNOWLEDGE_CATEGORIES.map((category) => (
                   <div key={category.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-all duration-300">
                     <div className="flex items-center mb-3">
                       <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center mr-3">
                         {category.icon}
                       </div>
                       <h3 className="font-semibold text-gray-900">{category.name}</h3>
                     </div>
                     <p className="text-sm text-gray-600">{category.description}</p>
                   </div>
                 ))}
               </div>
            </section>
          </div>
        </div>
      </main>

               {/* History Module */}
                 <section className="mb-8 bg-white px-4 py-8">
                  <div className="container mx-auto bg-white rounded-xl shadow-sm p-5 border border-gray-100">
                   <h3 className="text-lg font-semibold mb-4 flex items-center">
                     <Clock size={18} className="mr-2 text-blue-600" />
                     历史记录
                   </h3>
                   <div className="space-y-4">
                     {[
                       { id: 1, title: "企业版SaaS解决方案话术", time: "今天 14:30", type: "营销话术" },
                       { id: 2, title: "产品发布会直播脚本", time: "昨天 09:15", type: "直播脚本" },
                       { id: 3, title: "客户异议处理标准解答", time: "昨天 16:42", type: "售后服务" },
                       { id: 4, title: "短视频营销内容创作模板", time: "2023-10-18", type: "视频文案" },
                     ].map(item => (
                       <div key={item.id} className="flex items-start p-3 rounded-lg hover:bg-gray-50 transition-all duration-200 border border-transparent hover:border-gray-200">
                         <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-3 flex-shrink-0">
                           {item.type === "营销话术" && <FileText size={16} className="text-blue-600" />}
                           {item.type === "直播脚本" && <Mic size={16} className="text-blue-600" />}
                           {item.type === "视频文案" && <Video size={16} className="text-blue-600" />}
                           {item.type === "产品介绍" && <BookOpen size={16} className="text-blue-600" />}
                           {item.type === "售后服务" && <HelpCircle size={16} className="text-blue-600" />}
                           {item.type === "案例分享" && <Star size={16} className="text-blue-600" />}
                         </div>
                         <div className="flex-grow min-w-0">
                           <h4 className="text-sm font-medium text-gray-900 truncate">{item.title}</h4>
                           <div className="flex items-center mt-1 text-xs text-gray-500">
                             <span className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full">{item.type}</span>
                             <span className="ml-2">{item.time}</span>
                           </div>
                         </div>
                         <button className="text-gray-400 hover:text-blue-600 transition-colors ml-2 opacity-0 group-hover:opacity-100">
                           <MoreHorizontal size={16} />
                         </button>
                       </div>
                     ))}
                   </div>
                   <button className="w-full mt-4 text-sm text-blue-600 hover:text-blue-700 transition-colors py-2 rounded-lg hover:bg-blue-50">
                     查看全部历史
                   </button>
                 </div>
               </section>

       {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-6 mt-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center mb-4 md:mb-0">
              <BookOpen size={20} className="text-blue-600 mr-2" />
              <span className="text-gray-600 text-sm">© 2025 国华生物. 保留所有权利.</span>
            </div>
            
            <div className="flex space-x-6">
              <button className="text-gray-500 hover:text-gray-700 text-sm">使用帮助</button>
              <button className="text-gray-500 hover:text-gray-700 text-sm">隐私政策</button>
              <button className="text-gray-500 hover:text-gray-700 text-sm">联系我们</button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}