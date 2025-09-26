import React, { useState } from 'react';
import { Star, Copy, Share2, BookOpen, BookMarked } from 'lucide-react';
import { toast } from 'sonner';

interface KnowledgeItem {
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

interface KnowledgeCardProps {
  item: KnowledgeItem;
  onFavoriteToggle?: (id: number) => void;
}

export const KnowledgeCard: React.FC<KnowledgeCardProps> = ({ 
  item, 
  onFavoriteToggle 
}) => {
  const [copied, setCopied] = useState(false);
  const [isFavorite, setIsFavorite] = useState(!!item.isFavorite);
  
  const handleCopy = () => {
    // Simulate copy to clipboard
    navigator.clipboard.writeText(item.excerpt).then(() => {
      setCopied(true);
      toast.success('内容已复制到剪贴板');
      setTimeout(() => setCopied(false), 2000);
    });
  };
  
  const handleFavoriteToggle = () => {
    setIsFavorite(!isFavorite);
    if (onFavoriteToggle) {
      onFavoriteToggle(item.id);
    }
    toast.success(isFavorite ? '已取消收藏' : '已添加到收藏');
  };
  
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-all duration-300 transform hover:-translate-y-1">
      <div className="p-5">
        <div className="flex justify-between items-start mb-3">
          <span className="text-xs font-medium bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
            {item.category}
          </span>
          <button 
            className={`transition-colors ${isFavorite ? 'text-yellow-500' : 'text-gray-400 hover:text-yellow-500'}`}
            onClick={handleFavoriteToggle}
          >
            <Star size={16} fill={isFavorite ? "#facc15" : "none"} />
          </button>
        </div>
        
        <h3 className="font-semibold text-gray-900 mb-2 hover:text-blue-600 transition-colors cursor-pointer line-clamp-2">
          {item.title}
        </h3>
        
        <p className="text-sm text-gray-600 line-clamp-3 mb-4">
          {item.excerpt}
        </p>
        
        <div className="flex flex-wrap gap-2 mb-4">
          {item.tags.map((tag, idx) => (
            <span key={idx} className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full hover:bg-gray-200 transition-colors cursor-pointer">
              {tag}
            </span>
          ))}
        </div>
        
        <div className="flex justify-between items-center text-xs text-gray-500">
          <span>{item.updatedAt}</span>
          <div className="flex gap-3">
            <span className="flex items-center"><BookOpen size={14} className="mr-1" /> {item.views}</span>
            <span className="flex items-center"><BookMarked size={14} className="mr-1" /> {item.favorites}</span>
          </div>
        </div>
      </div>
      
      <div className="border-t border-gray-100 px-5 py-3 flex justify-between">
        <button 
          onClick={handleCopy}
          className={`text-sm transition-colors flex items-center ${copied ? 'text-green-600' : 'text-gray-600 hover:text-blue-600'}`}
        >
          <Copy size={14} className="mr-1" />
          {copied ? '已复制' : '复制内容'}
        </button>
        <button className="text-sm text-gray-600 hover:text-blue-600 transition-colors flex items-center">
          <Share2 size={14} className="mr-1" />
          分享
        </button>
      </div>
    </div>
  );
};

export default KnowledgeCard;