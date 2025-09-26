import React, { useState, useEffect } from 'react';
import { Search, X, Loader2 } from 'lucide-react';

interface SearchBarProps {
  initialValue?: string;
  onSearch: (query: string) => void;
  placeholder?: string;
  debounceDelay?: number;
}

const SearchBar: React.FC<SearchBarProps> = ({
  initialValue = '',
  onSearch,
  placeholder = '搜索知识库...',
  debounceDelay = 300
}) => {
  const [query, setQuery] = useState(initialValue);
  const [isSearching, setIsSearching] = useState(false);
  
  // Debounce search to prevent excessive calls
  useEffect(() => {
    if (!query.trim()) {
      onSearch('');
      return;
    }
    
    const timer = setTimeout(() => {
      setIsSearching(true);
      onSearch(query);
      // Simulate API call delay
      setTimeout(() => setIsSearching(false), 500);
    }, debounceDelay);
    
    return () => clearTimeout(timer);
  }, [query, onSearch, debounceDelay]);
  
  const handleClear = () => {
    setQuery('');
    onSearch('');
  };
  
  return (
    <div className="relative w-full">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        {isSearching ? (
          <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
        ) : (
          <Search className="h-4 w-4 text-gray-400" />
        )}
      </div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-full leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition-all"
        placeholder={placeholder}
      />
      {query && (
        <button
          type="button"
          className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-500 focus:outline-none"
          onClick={handleClear}
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
};

export default SearchBar;