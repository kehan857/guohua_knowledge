import React, { useState } from 'react';
import { FileText, RefreshCw, Settings } from 'lucide-react';
import { toast } from 'sonner';

import { useContext } from 'react';
import { AuthContext } from '@/contexts/authContext';

// 产品配置接口
interface Product {
  id: number;
  name: string;
  categories: string[];
}

// 场景配置接口
interface Scenario {
  id: number;
  name: string;
  products: string;
}

// 产品配置上下文
export const ProductConfigContext = React.createContext<{
  products: Product[];
  scenarios: Scenario[];
  setProducts: (products: Product[]) => void;
  setScenarios: (scenarios: Scenario[]) => void;
}>({
  products: [],
  scenarios: [],
  setProducts: () => {},
  setScenarios: () => {},
});

// 产品配置提供者组件
export const ProductConfigProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [products, setProducts] = useState<Product[]>([
    { id: 1, name: '企业版SaaS解决方案', categories: ['all', 'saas'] },
    { id: 2, name: '营销自动化工具', categories: ['all', 'marketing'] },
    { id: 3, name: '客户数据分析平台', categories: ['all', 'data'] },
  ]);
  
  const [scenarios, setScenarios] = useState<Scenario[]>([
    { id: 1, name: '初次接触', products: 'all' },
    { id: 2, name: '需求挖掘', products: 'all' },
    { id: 3, name: '方案介绍', products: 'all' },
    { id: 4, name: '异议处理', products: 'all' },
    { id: 5, name: '促成交易', products: 'all' },
  ]);
  
  return (
    <ProductConfigContext.Provider value={{ products, scenarios, setProducts, setScenarios }}>
      {children}
    </ProductConfigContext.Provider>
  );
};

// Mock generated scripts
const MOCK_SCRIPTS = {
  '1-1': `您好！我是[您的姓名]，来自[公司名称]。我们专注于为企业提供高效的SaaS解决方案，帮助像[客户公司]这样的企业提升运营效率。能否占用您几分钟时间简单了解一下您目前的业务系统使用情况？`,
  
  '1-3': `我们的企业版SaaS解决方案主要包含三个核心模块：首先是集成化的业务管理系统，能够打通您的销售、市场和客户服务数据；其次是智能化的数据分析平台，帮助您从数据中发现业务机会；最后是灵活的工作流引擎，可以根据您的业务流程自定义审批和协作流程。与传统系统相比，我们的方案部署更快，维护成本更低，并且支持按月付费模式。`,
  
  '2-5': `基于我们今天的交流，我建议您可以先从基础版开始使用，包含核心营销自动化功能，正好匹配您提到的需求。现在我们有季度优惠活动，首次签约可以享受8折优惠，并且包含3个月的免费实施服务。如果今天确认，我可以帮您锁定这个优惠价格，您看如何？`,
};

interface MarketingScriptGeneratorProps {
  className?: string;
}

const MarketingScriptGenerator: React.FC<MarketingScriptGeneratorProps> = ({ className = '' }) => {
  const [selectedProduct, setSelectedProduct] = useState<string>('');
  const [selectedScenario, setSelectedScenario] = useState<string>('');
  const [generatedScript, setGeneratedScript] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const { products, scenarios } = useContext(ProductConfigContext);
  const { isAuthenticated, userRole } = useContext(AuthContext);
  
  const handleGenerateScript = () => {
    if (!selectedProduct || !selectedScenario) {
      toast.error('请选择产品和场景');
      return;
    }
    
    setIsGenerating(true);
    
    // Simulate API call delay
    setTimeout(() => {
      const scriptKey = `${selectedProduct}-${selectedScenario}`;
      setGeneratedScript(MOCK_SCRIPTS[scriptKey as keyof typeof MOCK_SCRIPTS] || 
        `根据您选择的${products.find(p => p.id.toString() === selectedProduct)?.name}和${scenarios.find(s => s.id.toString() === selectedScenario)?.name}场景，我们为您生成了以下营销话术：\n\n[这里是根据您的具体需求生成的个性化营销话术内容，包含开场白、价值主张和下一步行动建议。]`);
      setIsGenerating(false);
    }, 1200);
  };
  
  const handleCopyScript = () => {
    if (!generatedScript) return;
    
    navigator.clipboard.writeText(generatedScript).then(() => {
      toast.success('话术已复制到剪贴板');
    }).catch(() => {
      toast.error('复制失败，请手动复制');
    });
  };
  
  // 产品配置按钮 - 仅管理员可见
  const renderProductConfigButton = () => {
    if (userRole !== 'admin') return null;
    
    return (
      <button className="absolute top-4 right-4 text-sm text-blue-600 hover:text-blue-800">
        <Settings size={16} className="inline mr-1" />
        配置产品
      </button>
    );
  };
  
  return (
    <div className={`bg-white rounded-xl shadow-sm p-5 border border-gray-100 ${className} relative`}>
      {renderProductConfigButton()}
      <h3 className="text-lg font-semibold mb-4 flex items-center">
        <FileText size={18} className="mr-2 text-blue-600" />
        营销话术生成器
      </h3>
      
      <div className="space-y-4 mb-5">
        <div>
          <label className="text-sm font-medium text-gray-700 block mb-1">产品选择</label>
          <select 
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
            value={selectedProduct}
            onChange={(e) => setSelectedProduct(e.target.value)}
          >
            <option value="">请选择产品</option>
            {products.map(product => (
              <option key={product.id} value={product.id.toString()}>
                {product.name}
              </option>
            ))}
          </select>
        </div>
        
        <div>
          <label className="text-sm font-medium text-gray-700 block mb-1">场景选择</label>
          <select 
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
          >
            <option value="">请选择场景</option>
            {scenarios.map(scenario => (
              <option key={scenario.id} value={scenario.id.toString()}>
                {scenario.name}
              </option>
            ))}
          </select>
        </div>
        
        <button 
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center justify-center"
          onClick={handleGenerateScript}
          disabled={isGenerating}
        >
          {isGenerating ? (
            <>
              <RefreshCw size={16} className="mr-2 animate-spin" />
              生成中...
            </>
          ) : (
            '生成话术'
          )}
        </button>
      </div>
      
      {generatedScript && (
        <div className="mt-6 pt-5 border-t border-gray-100">
          <h4 className="text-sm font-medium text-gray-900 mb-2">生成结果</h4>
          <div className="bg-gray-50 p-4 rounded-lg text-sm text-gray-800 font-medium min-h-[120px] whitespace-pre-wrap mb-3">
            {generatedScript}
          </div>
          <button 
            className="w-full bg-gray-100 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium flex items-center justify-center"
            onClick={handleCopyScript}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
            </svg>
            复制话术
          </button>
        </div>
      )}
    </div>
  );
};

export default MarketingScriptGenerator;