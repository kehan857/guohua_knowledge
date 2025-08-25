"""
AI服务集成
负责与FastGPT和其他AI服务的集成，处理对话、成本计算等
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import httpx

from app.core.config import settings
from app.core.redis import redis_client
from app.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """AI服务异常"""
    def __init__(self, message: str, status_code: int = None, response_data: Dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class TokenCalculator:
    """Token计算器"""
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """估算文本的token数量（简化算法）"""
        if not text:
            return 0
        
        # 中文字符按1.5个token计算，英文单词按平均token计算
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_chars = len(text) - chinese_chars
        
        # 简化计算：中文1.5token/字，英文4字符/token
        chinese_tokens = chinese_chars * 1.5
        english_tokens = english_chars / 4
        
        return int(chinese_tokens + english_tokens)
    
    @staticmethod
    def calculate_cost(
        input_tokens: int,
        output_tokens: int,
        model_name: str
    ) -> float:
        """计算API调用成本"""
        pricing = settings.AI_MODELS_PRICING.get(model_name, {})
        
        if not pricing:
            logger.warning(f"未找到模型 {model_name} 的价格配置")
            return 0.0
        
        input_cost = (input_tokens / 1000) * pricing.get("input_price_per_1k", 0)
        output_cost = (output_tokens / 1000) * pricing.get("output_price_per_1k", 0)
        
        return round(input_cost + output_cost, 6)


class AIService:
    """AI服务主类"""
    
    def __init__(self):
        self.base_url = settings.AI_SERVICE_ENDPOINT
        self.api_key = settings.AI_SERVICE_KEY
        self.default_model = settings.AI_DEFAULT_MODEL
        self.timeout = settings.AI_REQUEST_TIMEOUT
        self.max_retries = settings.AI_MAX_RETRIES
        
        # 创建HTTP客户端
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )
        
        # 创建限流器（防止API过载）
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=100,  # 每分钟最多100次请求
            max_requests_per_hour=3000    # 每小时最多3000次请求
        )
        
        # Token计算器
        self.token_calculator = TokenCalculator()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_connection(self) -> bool:
        """测试AI服务连接"""
        try:
            result = await self._make_request("GET", "/health")
            return result.get("status") == "ok"
        except Exception as e:
            logger.error(f"AI服务连接测试失败: {str(e)}")
            return False
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """发起AI API请求"""
        
        # 限流控制
        await self.rate_limiter.acquire()
        
        try:
            logger.debug(f"AI API请求: {method} {endpoint}")
            
            # 发起请求
            response = await self.client.request(
                method=method,
                url=endpoint,
                json=data if method.upper() in ["POST", "PUT", "PATCH"] else None
            )
            
            # 检查响应状态
            if response.status_code >= 400:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    pass
                
                raise AIServiceError(
                    message=f"AI API请求失败: {response.status_code}",
                    status_code=response.status_code,
                    response_data=error_data
                )
            
            # 解析响应
            result = response.json()
            
            logger.debug(f"AI API响应成功: {endpoint}")
            return result
            
        except httpx.TimeoutException:
            logger.warning(f"AI API请求超时: {endpoint}")
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)
                return await self._make_request(method, endpoint, data, retry_count + 1)
            raise AIServiceError("请求超时")
            
        except httpx.NetworkError as e:
            logger.warning(f"AI API网络错误: {endpoint}, {str(e)}")
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)
                return await self._make_request(method, endpoint, data, retry_count + 1)
            raise AIServiceError(f"网络错误: {str(e)}")
            
        except AIServiceError:
            raise
        except Exception as e:
            logger.error(f"AI API请求异常: {endpoint}, {str(e)}")
            raise AIServiceError(f"请求异常: {str(e)}")
    
    async def process_message(
        self,
        user_message: str,
        context: Dict[str, Any],
        workflow_id: str = None,
        model_name: str = None
    ) -> Dict[str, Any]:
        """处理用户消息，获取AI回复"""
        try:
            start_time = time.time()
            
            # 使用指定的工作流或默认工作流
            workflow_id = workflow_id or "default"
            model_name = model_name or self.default_model
            
            # 构建请求数据
            request_data = {
                "userChatInput": user_message,
                "variables": self._build_variables(context),
                "workflowId": workflow_id,
                "model": model_name
            }
            
            # 估算输入token数
            input_text = user_message + json.dumps(context, ensure_ascii=False)
            estimated_input_tokens = self.token_calculator.estimate_tokens(input_text)
            
            # 调用AI API
            result = await self._make_request("POST", "/chat/completions", request_data)
            
            # 计算处理时间
            processing_time = int((time.time() - start_time) * 1000)
            
            # 解析响应
            ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 获取token使用情况
            usage = result.get("usage", {})
            actual_input_tokens = usage.get("prompt_tokens", estimated_input_tokens)
            output_tokens = usage.get("completion_tokens", 0)
            
            # 估算输出token（如果API未返回）
            if output_tokens == 0:
                output_tokens = self.token_calculator.estimate_tokens(ai_response)
            
            # 计算成本
            cost = self.token_calculator.calculate_cost(
                actual_input_tokens,
                output_tokens,
                model_name
            )
            
            # 分析意图和情感（简化实现）
            intent_info = await self._analyze_intent(user_message)
            
            logger.info(f"AI消息处理成功，耗时: {processing_time}ms，成本: ${cost}")
            
            return {
                "success": True,
                "response": ai_response,
                "processing_time": processing_time,
                "tokens": {
                    "input": actual_input_tokens,
                    "output": output_tokens,
                    "total": actual_input_tokens + output_tokens
                },
                "cost": cost,
                "model": model_name,
                "workflow_id": workflow_id,
                "intent": intent_info.get("intent"),
                "sentiment": intent_info.get("sentiment"),
                "keywords": intent_info.get("keywords", [])
            }
            
        except AIServiceError:
            raise
        except Exception as e:
            logger.error(f"AI消息处理失败: {str(e)}")
            raise AIServiceError(f"消息处理失败: {str(e)}")
    
    def _build_variables(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """构建AI工作流所需的变量"""
        variables = {
            "role": context.get("role", "销售助手"),
            "nickName": context.get("contact_nickname", "朋友"),
            "accountNo": context.get("account_id", ""),
            "nickId": context.get("contact_wxid", ""),
            "histories": self._format_chat_history(context.get("chat_history", [])),
        }
        
        # 添加图片URL（如果有）
        if context.get("image_url"):
            variables["picture"] = context["image_url"]
        
        # 添加用户自定义变量
        if context.get("custom_variables"):
            variables.update(context["custom_variables"])
        
        return variables
    
    def _format_chat_history(self, chat_history: List[Dict[str, Any]]) -> str:
        """格式化聊天历史为AI可理解的文本"""
        if not chat_history:
            return ""
        
        formatted_history = []
        for msg in chat_history[-10:]:  # 只取最近10条消息
            role = "用户" if msg.get("direction") == "incoming" else "我"
            content = msg.get("content", "")
            timestamp = msg.get("created_at", "")
            
            if content:
                formatted_history.append(f"{role}({timestamp}): {content}")
        
        return "\n".join(formatted_history)
    
    async def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """分析消息意图和情感（简化实现）"""
        try:
            # 这里可以集成更复杂的NLP分析
            # 目前使用简单的关键词匹配
            
            # 意图分类
            intent = "general"
            if any(word in message for word in ["价格", "多少钱", "费用", "收费"]):
                intent = "inquiry_price"
            elif any(word in message for word in ["购买", "要买", "下单"]):
                intent = "purchase_intent"
            elif any(word in message for word in ["咨询", "了解", "介绍"]):
                intent = "inquiry_product"
            elif any(word in message for word in ["投诉", "问题", "故障"]):
                intent = "complaint"
            
            # 情感分析
            sentiment = "neutral"
            positive_words = ["好", "不错", "满意", "喜欢", "感谢"]
            negative_words = ["差", "不好", "失望", "生气", "烂"]
            
            if any(word in message for word in positive_words):
                sentiment = "positive"
            elif any(word in message for word in negative_words):
                sentiment = "negative"
            
            # 关键词提取（简化）
            keywords = []
            for word in ["产品", "服务", "价格", "质量", "售后"]:
                if word in message:
                    keywords.append(word)
            
            return {
                "intent": intent,
                "sentiment": sentiment,
                "keywords": keywords
            }
            
        except Exception as e:
            logger.warning(f"意图分析失败: {str(e)}")
            return {
                "intent": "general",
                "sentiment": "neutral",
                "keywords": []
            }
    
    async def batch_process_messages(
        self,
        messages: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """批量处理消息"""
        try:
            # 创建任务队列
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_single_message(msg_data):
                async with semaphore:
                    try:
                        return await self.process_message(
                            user_message=msg_data["content"],
                            context=msg_data["context"],
                            workflow_id=msg_data.get("workflow_id"),
                            model_name=msg_data.get("model_name")
                        )
                    except Exception as e:
                        logger.error(f"批量处理消息失败: {msg_data.get('id')}, {str(e)}")
                        return {
                            "success": False,
                            "error": str(e),
                            "message_id": msg_data.get("id")
                        }
            
            # 并发处理
            tasks = [process_single_message(msg) for msg in messages]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return results
            
        except Exception as e:
            logger.error(f"批量处理消息异常: {str(e)}")
            raise AIServiceError(f"批量处理失败: {str(e)}")
    
    async def get_conversation_summary(
        self,
        chat_history: List[Dict[str, Any]],
        summary_type: str = "daily"
    ) -> Dict[str, Any]:
        """生成对话摘要"""
        try:
            if not chat_history:
                return {"summary": "无对话记录", "key_points": []}
            
            # 格式化聊天历史
            formatted_history = self._format_chat_history(chat_history)
            
            # 构建摘要请求
            prompt = f"""
            请为以下对话生成摘要，包括：
            1. 对话主要内容
            2. 关键话题
            3. 用户意向
            4. 需要跟进的事项
            
            对话记录：
            {formatted_history}
            
            请以JSON格式返回，包含summary、key_topics、user_intent、action_items字段。
            """
            
            request_data = {
                "userChatInput": prompt,
                "variables": {"role": "对话分析助手"},
                "model": self.default_model
            }
            
            result = await self._make_request("POST", "/chat/completions", request_data)
            
            # 解析AI返回的摘要
            ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            try:
                # 尝试解析JSON格式的回复
                summary_data = json.loads(ai_response)
            except:
                # 如果不是JSON格式，使用文本作为摘要
                summary_data = {
                    "summary": ai_response,
                    "key_topics": [],
                    "user_intent": "unknown",
                    "action_items": []
                }
            
            return summary_data
            
        except Exception as e:
            logger.error(f"生成对话摘要失败: {str(e)}")
            return {
                "summary": "摘要生成失败",
                "key_topics": [],
                "user_intent": "unknown",
                "action_items": []
            }
    
    async def check_content_safety(self, content: str) -> Dict[str, Any]:
        """内容安全检查"""
        try:
            # 这里可以集成内容审核API
            # 目前使用简单的关键词过滤
            
            unsafe_keywords = ["政治", "暴力", "色情", "赌博", "诈骗"]
            is_safe = not any(keyword in content for keyword in unsafe_keywords)
            
            if not is_safe:
                logger.warning(f"检测到不安全内容: {content[:50]}...")
            
            return {
                "is_safe": is_safe,
                "confidence": 0.9 if is_safe else 0.1,
                "categories": [] if is_safe else ["unsafe_content"]
            }
            
        except Exception as e:
            logger.error(f"内容安全检查失败: {str(e)}")
            return {
                "is_safe": True,  # 检查失败时默认认为安全
                "confidence": 0.5,
                "categories": []
            }
    
    async def get_model_list(self) -> List[Dict[str, Any]]:
        """获取可用的AI模型列表"""
        try:
            result = await self._make_request("GET", "/models")
            return result.get("data", [])
        except Exception as e:
            logger.error(f"获取模型列表失败: {str(e)}")
            return []
    
    async def get_workflow_list(self) -> List[Dict[str, Any]]:
        """获取可用的工作流列表"""
        try:
            result = await self._make_request("GET", "/workflows")
            return result.get("data", [])
        except Exception as e:
            logger.error(f"获取工作流列表失败: {str(e)}")
            return []
    
    async def estimate_tokens_for_text(self, text: str) -> int:
        """估算文本的token数量"""
        return self.token_calculator.estimate_tokens(text)
    
    async def calculate_cost_for_tokens(
        self,
        input_tokens: int,
        output_tokens: int,
        model_name: str = None
    ) -> float:
        """计算指定token数量的成本"""
        model_name = model_name or self.default_model
        return self.token_calculator.calculate_cost(input_tokens, output_tokens, model_name)


# 全局AI服务实例
ai_service = AIService()

