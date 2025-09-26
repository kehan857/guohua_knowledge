import { Routes, Route } from "react-router-dom";
import { Link } from "react-router-dom";
import Home from "@/pages/Home";
import { useState } from "react";
import { AuthContext } from '@/contexts/authContext';
import { ProductConfigProvider } from '@/components/knowledge/MarketingScriptGenerator';

// 占位组件 - 实际项目中应替换为真实组件
const ScriptGenerator = () => <div className="container mx-auto px-4 py-8">
  <h1 className="text-2xl font-bold mb-6">营销话术生成器</h1>
  <div className="bg-gray-100 p-8 text-center rounded-xl">
    <p className="text-gray-500">营销话术生成器页面内容</p>
    <Link to="/" className="inline-block mt-4 text-blue-600 hover:underline">返回首页</Link>
  </div>
</div>;

const VideoScripts = () => <div className="container mx-auto px-4 py-8">
  <h1 className="text-2xl font-bold mb-6">视频脚本模板</h1>
  <div className="bg-gray-100 p-8 text-center rounded-xl">
    <p className="text-gray-500">视频脚本模板页面内容</p>
    <Link to="/" className="inline-block mt-4 text-blue-600 hover:underline">返回首页</Link>
  </div>
</div>;

const LiveGuides = () => <div className="container mx-auto px-4 py-8">
  <h1 className="text-2xl font-bold mb-6">直播话术指南</h1>
  <div className="bg-gray-100 p-8 text-center rounded-xl">
    <p className="text-gray-500">直播话术指南页面内容</p>
    <Link to="/" className="inline-block mt-4 text-blue-600 hover:underline">返回首页</Link>
  </div>
</div>;

const Favorites = () => <div className="container mx-auto px-4 py-8">
  <h1 className="text-2xl font-bold mb-6">我的收藏</h1>
  <div className="bg-gray-100 p-8 text-center rounded-xl">
    <p className="text-gray-500">我的收藏页面内容</p>
    <Link to="/" className="inline-block mt-4 text-blue-600 hover:underline">返回首页</Link>
  </div>
</div>;

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [userRole, setUserRole] = useState('sales'); // 'sales' or 'admin'

  const logout = () => {
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider
      value={{ isAuthenticated, setIsAuthenticated, logout, userRole, setUserRole }}
    >
      <ProductConfigProvider>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/script-generator" element={<ScriptGenerator />} />
          <Route path="/video-scripts" element={<VideoScripts />} />
          <Route path="/live-guides" element={<LiveGuides />} />
          <Route path="/favorites" element={<Favorites />} />
          <Route path="/other" element={<div className="text-center text-xl">Other Page - Coming Soon</div>} />
        </Routes>
      </ProductConfigProvider>
    </AuthContext.Provider>
  );
}
