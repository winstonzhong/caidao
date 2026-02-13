#!/usr/bin/env python3
"""
文本分类客户端工具

基于 /home/yka-003/workspace/sg/text_classifier 服务的 HTTP API 接口
外部URL: https://wv.j1.sale/classify/

用法:
    >>> from tool_text_classifier import classify_text, batch_classify, match_category
    >>> result = classify_text("这是一条测试文本")
    >>> print(result)
    {'category': '测试', 'confidence': 0.95, 'similarity': 0.92}
    
    >>> results = batch_classify(["文本1", "文本2", "文本3"])
    >>> print(results)
    [{'category': '类别A', ...}, {'category': '类别B', ...}, ...]
    
    >>> # 检查文本是否匹配指定类别
    >>> is_match = match_category("抖音短视频很有趣", "娱乐")
    >>> print(is_match)
    True
"""

import json
import time
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

import requests


# 默认配置
DEFAULT_BASE_URL = "https://wv.j1.sale"
DEFAULT_TIMEOUT = 30


@dataclass
class ClassifyResult:
    """文本分类结果"""
    text: str
    category_id: int
    category_name: str
    similarity: float
    is_default: bool
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'text': self.text,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'similarity': self.similarity,
            'is_default': self.is_default,
        }


class TextClassifierClient:
    """
    文本分类客户端
    
    封装对文本分类服务的 HTTP API 调用
    
    Example:
        >>> client = TextClassifierClient(base_url="https://wv.j1.sale")
        >>> result = client.classify("这是一条测试文本")
        >>> print(result.category)
        '测试类别'
    """
    
    def __init__(self, 
                 base_url: str = DEFAULT_BASE_URL,
                 timeout: int = DEFAULT_TIMEOUT,
                 admin_token: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            base_url: 服务基础URL
            timeout: 请求超时时间（秒）
            admin_token: 管理员Token（用于管理操作）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.admin_token = admin_token
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
    
    def _make_request(self, 
                     method: str, 
                     endpoint: str, 
                     data: Optional[Dict] = None,
                     params: Optional[Dict] = None) -> Dict:
        """
        发送 HTTP 请求
        
        Args:
            method: 请求方法 (GET/POST/PUT/DELETE)
            endpoint: API 端点
            data: 请求体数据
            params: URL 参数
            
        Returns:
            响应数据
            
        Raises:
            requests.RequestException: 请求失败
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise requests.RequestException(f"请求超时 ({self.timeout}秒)")
        except requests.exceptions.ConnectionError:
            raise requests.RequestException(f"连接失败: {url}")
        except requests.exceptions.HTTPError as e:
            raise requests.RequestException(f"HTTP错误: {e.response.status_code} - {e.response.text}")
        except json.JSONDecodeError:
            raise requests.RequestException("响应解析失败")
    
    def classify(self, 
                text: str, 
                top_k: int = 3,
                return_vector: bool = False) -> ClassifyResult:
        """
        单条文本分类
        
        Args:
            text: 待分类文本
            top_k: 返回前K个相似类别
            return_vector: 是否返回向量
            
        Returns:
            分类结果
            
        Example:
            >>> client = TextClassifierClient()
            >>> result = client.classify("抖音短视频很有趣")
            >>> print(f"类别: {result.category}, 置信度: {result.confidence}")
        """
        data = {
            'text': text,
            'top_k': top_k,
            'return_vector': return_vector
        }
        
        response = self._make_request('POST', '/classify/', data=data)
        
        if response.get('code') != 200:
            raise requests.RequestException(f"API错误: {response.get('message', '未知错误')}")
        
        result_data = response.get('data', {})
        
        return ClassifyResult(
            text=text,
            category_id=result_data.get('category_id', 0),
            category_name=result_data.get('category_name', ''),
            similarity=result_data.get('similarity', 0.0),
            is_default=result_data.get('is_default', False),
        )
    
    def batch_classify(self, 
                      texts: List[str], 
                      top_k: int = 3) -> List[ClassifyResult]:
        """
        批量文本分类
        
        Args:
            texts: 待分类文本列表
            top_k: 返回前K个相似类别
            
        Returns:
            分类结果列表
            
        Example:
            >>> client = TextClassifierClient()
            >>> texts = ["抖音很好玩", "今天天气不错", "股票涨了"]
            >>> results = client.batch_classify(texts)
            >>> for r in results:
            ...     print(f"{r.text} -> {r.category}")
        """
        results = []
        for text in texts:
            try:
                result = self.classify(text, top_k=top_k)
                results.append(result)
            except Exception as e:
                # 单条失败时记录错误但不中断
                results.append(ClassifyResult(
                    text=text,
                    category_id=-1,
                    category_name='ERROR',
                    similarity=0.0,
                    is_default=False,
                ))
        return results
    
    def health_check(self) -> Dict:
        """
        健康检查
        
        Returns:
            服务状态信息
            
        Example:
            >>> client = TextClassifierClient()
            >>> status = client.health_check()
            >>> print(status['status'])
            'ok'
        """
        return self._make_request('GET', '/health')
    
    def get_categories(self) -> List[Dict]:
        """
        获取所有类别
        
        Returns:
            类别列表
            
        Example:
            >>> client = TextClassifierClient()
            >>> categories = client.get_categories()
            >>> for cat in categories:
            ...     print(f"{cat['name']}: {cat['description']}")
        """
        response = self._make_request('GET', '/categories/')
        return response if isinstance(response, list) else []
    
    def add_category(self, 
                    name: str, 
                    description: str = "",
                    sample_texts: Optional[List[str]] = None) -> Dict:
        """
        添加新类别（需要管理员Token）
        
        Args:
            name: 类别名称
            description: 类别描述
            sample_texts: 示例文本列表
            
        Returns:
            添加结果
            
        Raises:
            ValueError: 未设置 admin_token
        """
        if not self.admin_token:
            raise ValueError("需要提供 admin_token 才能添加类别")
        
        data = {
            'name': name,
            'description': description,
            'sample_texts': sample_texts or []
        }
        
        headers = {'X-Admin-Token': self.admin_token}
        response = self._make_request('POST', '/categories/', data=data)
        return response
    
    def delete_category(self, category_id: int) -> Dict:
        """
        删除类别（需要管理员Token）
        
        Args:
            category_id: 类别ID
            
        Raises:
            ValueError: 未设置 admin_token
        """
        if not self.admin_token:
            raise ValueError("需要提供 admin_token 才能删除类别")
        
        return self._make_request('DELETE', f'/categories/{category_id}')


# ==================== 便捷函数 ====================

def classify_text(text: str, 
                 base_url: str = DEFAULT_BASE_URL,
                 top_k: int = 3) -> Dict:
    """
    单条文本分类（便捷函数）
    
    Args:
        text: 待分类文本
        base_url: 服务URL
        top_k: 返回前K个结果
        
    Returns:
        分类结果字典
        
    Example:
        >>> result = classify_text("抖音短视频很有趣")
        >>> print(result['category'])
        '娱乐'
    """
    client = TextClassifierClient(base_url=base_url)
    result = client.classify(text, top_k=top_k)
    return result.to_dict()


def batch_classify(texts: List[str],
                  base_url: str = DEFAULT_BASE_URL,
                  top_k: int = 3) -> List[Dict]:
    """
    批量文本分类（便捷函数）
    
    Args:
        texts: 待分类文本列表
        base_url: 服务URL
        top_k: 返回前K个结果
        
    Returns:
        分类结果字典列表
        
    Example:
        >>> texts = ["抖音很好玩", "今天天气不错"]
        >>> results = batch_classify(texts)
        >>> for r in results:
        ...     print(f"{r['text']} -> {r['category']}")
    """
    client = TextClassifierClient(base_url=base_url)
    results = client.batch_classify(texts, top_k=top_k)
    return [r.to_dict() for r in results]


def check_service(base_url: str = DEFAULT_BASE_URL) -> bool:
    """
    检查服务是否可用
    
    Args:
        base_url: 服务URL
        
    Returns:
        服务是否可用
        
    Example:
        >>> if check_service():
        ...     print("服务正常")
        ... else:
        ...     print("服务不可用")
    """
    try:
        client = TextClassifierClient(base_url=base_url, timeout=5)
        status = client.health_check()
        return status.get('status') == 'ok'
    except Exception:
        return False


def match_category(text: str,
                   category: str,
                   top_k: int = 3,
                   min_similarity: float = 0.85,
                   base_url: str = DEFAULT_BASE_URL) -> bool:
    """
    检查文本是否匹配指定类别（快捷函数）
    
    对文本进行分类，判断在top_k个结果中，相似度大于等于min_similarity的结果
    中是否存在指定的category
    
    Args:
        text: 待分类文本
        category: 需要匹配的类别名称
        top_k: 返回前K个结果进行检查，默认为3
        min_similarity: 最小相似度阈值，默认为0.85
        base_url: 服务URL
        
    Returns:
        如果存在匹配的类别则返回True，否则返回False
        
    Example:
        >>> # 检查文本是否属于"娱乐"类别（相似度>=0.85）
        >>> if match_category("抖音短视频很有趣", "娱乐"):
        ...     print("属于娱乐类别")
        ... else:
        ...     print("不属于娱乐类别或相似度不够")
        >>> 
        >>> # 使用自定义参数
        >>> match_category("股票大涨", "财经", top_k=5, min_similarity=0.9)
        False
    """
    client = TextClassifierClient(base_url=base_url)
    
    # 准备请求数据
    data = {
        'text': text,
        'top_k': top_k,
        'return_vector': False
    }
    
    try:
        response = client._make_request('POST', '/classify/', data=data)
        
        if response.get('code') != 200:
            return False
        
        result_data = response.get('data', {})
        
        # 获取top_k结果列表
        top_results = result_data.get('top_k_results', [])
        
        # 如果没有top_k_results，尝试从单个结果构建
        if not top_results and result_data.get('category_name'):
            top_results = [{
                'category_id': result_data.get('category_id'),
                'category_name': result_data.get('category_name'),
                'similarity': result_data.get('similarity', 0.0)
            }]
        
        # 检查是否有符合条件的匹配
        for result in top_results:
            cat_name = result.get('category_name', '')
            similarity = result.get('similarity', 0.0)
            
            if similarity >= min_similarity and cat_name == category:
                return True
        
        return False
        
    except Exception:
        return False


# ==================== 测试代码 ====================

def _run_tests():
    """运行测试"""
    print("=" * 60)
    print("文本分类客户端测试")
    print("=" * 60)
    
    # 测试配置
    base_url = DEFAULT_BASE_URL
    test_texts = [
        "抖音短视频真的很有趣，每天都要刷好久",
        "今天股市大涨，赚了不少钱",
        "这家餐厅的菜味道真不错，推荐给大家",
        "天气预报说明天会下雨，记得带伞",
    ]
    
    # 1. 测试健康检查
    print("\n1. 测试健康检查...")
    try:
        client = TextClassifierClient(base_url=base_url, timeout=10)
        status = client.health_check()
        print(f"   ✅ 服务状态: {status.get('status', 'unknown')}")
        print(f"   词向量维度: {status.get('vector_dim', 'N/A')}")
        print(f"   类别数量: {status.get('category_count', 'N/A')}")
    except Exception as e:
        print(f"   ❌ 健康检查失败: {e}")
        print("   跳过后续测试")
        return
    
    # 2. 测试单条分类
    print("\n2. 测试单条文本分类...")
    for text in test_texts[:2]:
        try:
            result = client.classify(text, top_k=3)
            print(f"   文本: {text[:30]}...")
            print(f"   类别ID: {result.category_id}, 类别名: {result.category_name}, 相似度: {result.similarity:.4f}")
            if result.is_default:
                print(f"   ⚠️  使用默认类别")
        except Exception as e:
            print(f"   ❌ 分类失败: {e}")
    
    # 3. 测试批量分类
    print("\n3. 测试批量文本分类...")
    try:
        start_time = time.time()
        results = client.batch_classify(test_texts, top_k=2)
        elapsed = time.time() - start_time
        print(f"   分类 {len(test_texts)} 条文本，耗时: {elapsed:.2f}秒")
        for i, result in enumerate(results):
            print(f"   [{i+1}] {result.text[:25]}... -> {result.category_name} (相似度: {result.similarity:.2f})")
    except Exception as e:
        print(f"   ❌ 批量分类失败: {e}")
    
    # 4. 测试便捷函数
    print("\n4. 测试便捷函数...")
    try:
        result = classify_text(test_texts[0], base_url=base_url)
        print(f"   classify_text: {result['text'][:25]}... -> {result['category_name']}")
        
        results = batch_classify(test_texts[:2], base_url=base_url)
        print(f"   batch_classify: 成功分类 {len(results)} 条文本")
    except Exception as e:
        print(f"   ❌ 便捷函数测试失败: {e}")
    
    # 5. 测试获取类别列表
    print("\n5. 测试获取类别列表...")
    try:
        categories = client.get_categories()
        print(f"   共有 {len(categories)} 个类别")
        for cat in categories[:5]:  # 只显示前5个
            print(f"   - {cat.get('name', 'N/A')}: {cat.get('description', 'N/A')[:30]}...")
    except Exception as e:
        print(f"   ❌ 获取类别失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    # 运行测试
    _run_tests()
