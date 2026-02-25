# encoding: utf-8
"""
抖音 XML 解析工具模块

用于解析抖音视频页面的 XML 结构，提取关键节点信息。
不依赖临时资源ID，而是使用稳定的特征如 content-desc、层级结构、位置等。

用法示例:
    >>> from tool_dy_xml import 提取xml中的视频节点
    >>> from pathlib import Path
    >>> xml_file = Path(__file__).parent / "ut" / "xmls" / "20260225_164300.xml"
    >>> node = 提取xml中的视频节点(xml_file)
    >>> node is not None
    True
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Union, List, Tuple
import re
import json


def 提取xml中的视频节点(xml_source: Union[ET.ElementTree, ET.Element, str, Path]) -> Optional[ET.Element]:
    """
    从抖音 XML 中提取视频页面核心容器节点（ViewPager）
    
    该函数通过以下稳定特征识别视频节点：
    - resource-id 包含 "viewpager" (这是Android标准组件名，相对稳定)
    - content-desc 等于 "视频"
    
    Args:
        xml_source: XML 源，可以是：
            - xml.etree.ElementTree.ElementTree 对象
            - xml.etree.ElementTree.Element 对象
            - XML 文件路径（str 或 Path）
    
    Returns:
        找到的视频容器节点（ET.Element），未找到返回 None
        
    Raises:
        FileNotFoundError: 当提供的文件路径不存在时
        ET.ParseError: 当 XML 解析失败时
    
    Examples:
        >>> # 测试用例1：从文件路径加载
        >>> current_dir = Path(__file__).parent
        >>> xml_dir = current_dir / "ut" / "xmls"
        >>> test_file = xml_dir / "20260225_164300.xml"
        >>> 
        >>> node = 提取xml中的视频节点(test_file)
        >>> node is not None
        True
        >>> node.get('resource-id')
        'com.ss.android.ugc.aweme:id/viewpager'
        >>> node.get('content-desc')
        '视频'
        >>> 'ViewPager' in node.get('class', '')
        True
        
        >>> # 测试用例2：从 ElementTree 加载
        >>> tree = ET.parse(test_file)
        >>> node2 = 提取xml中的视频节点(tree)
        >>> node2 is not None
        True
        >>> node2.get('resource-id') == node.get('resource-id')
        True
        
        >>> # 测试用例3：从 Element 加载
        >>> root = tree.getroot()
        >>> node3 = 提取xml中的视频节点(root)
        >>> node3 is not None
        True
        
        >>> # 测试用例4：遍历目录中所有 XML 文件
        >>> xml_files = list(xml_dir.glob("*.xml"))
        >>> len(xml_files) >= 1
        True
        >>> 
        >>> results = []
        >>> for xml_file in xml_files:
        ...     n = 提取xml中的视频节点(xml_file)
        ...     results.append({
        ...         'file': xml_file.name,
        ...         'found': n is not None,
        ...         'resource_id': n.get('resource-id') if n is not None else None,
        ...         'content_desc': n.get('content-desc') if n is not None else None
        ...     })
        >>> 
        >>> # 验证所有文件都能找到视频节点
        >>> all(r['found'] for r in results)
        True
        >>> 
        >>> # 验证所有节点都有正确的特征
        >>> all(r['resource_id'] == 'com.ss.android.ugc.aweme:id/viewpager' for r in results)
        True
        >>> all(r['content_desc'] == '视频' for r in results)
        True
    """
    # 处理不同类型的输入
    if isinstance(xml_source, (str, Path)):
        tree = ET.parse(xml_source)
        root = tree.getroot()
    elif isinstance(xml_source, ET.ElementTree):
        root = xml_source.getroot()
    elif isinstance(xml_source, ET.Element):
        root = xml_source
    else:
        raise TypeError(f"不支持的输入类型: {type(xml_source)}")
    
    return _递归查找视频节点(root)


def _递归查找视频节点(node: ET.Element) -> Optional[ET.Element]:
    """
    递归查找符合视频特征的节点
    
    识别标准：
    1. resource-id 包含 "viewpager" (Android标准组件名)
    2. content-desc 等于 "视频"
    """
    resource_id = node.get('resource-id', '')
    content_desc = node.get('content-desc', '')
    
    # 检查是否为视频容器节点
    if ('viewpager' in resource_id.lower() and 
        content_desc == '视频' and
        'com.ss.android.ugc.aweme' in resource_id):
        return node
    
    # 递归查找子节点
    for child in node:
        result = _递归查找视频节点(child)
        if result is not None:
            return result
    
    return None


def 获取节点特征值(node: ET.Element) -> dict:
    """
    获取视频节点的唯一特征值
    
    Args:
        node: XML 节点
    
    Returns:
        包含节点特征的字典
    
    Examples:
        >>> # 测试所有 XML 文件的节点特征
        >>> current_dir = Path(__file__).parent
        >>> xml_dir = current_dir / "ut" / "xmls"
        >>> xml_files = list(xml_dir.glob("*.xml"))
        >>> 
        >>> all_features = []
        >>> for xml_file in xml_files:
        ...     node = 提取xml中的视频节点(xml_file)
        ...     if node:
        ...         features = 获取节点特征值(node)
        ...         all_features.append(features)
        >>> 
        >>> len(all_features) == len(xml_files)
        True
        >>> all(f['resource_id'] == 'com.ss.android.ugc.aweme:id/viewpager' for f in all_features)
        True
        >>> all(f['content_desc'] == '视频' for f in all_features)
        True
        >>> all('ViewPager' in f['class'] for f in all_features)
        True
        >>> all('bounds' in f for f in all_features)
        True
    """
    return {
        'resource_id': node.get('resource-id', ''),
        'content_desc': node.get('content-desc', ''),
        'class': node.get('class', ''),
        'bounds': node.get('bounds', ''),
        'package': node.get('package', '')
    }


def 提取节点内所有文字(node: ET.Element) -> list:
    """
    提取节点及其所有子节点中的文字信息
    
    Args:
        node: XML 节点
    
    Returns:
        文字信息列表，每项为 (类型, 内容) 元组
    
    Examples:
        >>> # 测试所有 XML 文件的文字提取
        >>> current_dir = Path(__file__).parent
        >>> xml_dir = current_dir / "ut" / "xmls"
        >>> xml_files = list(xml_dir.glob("*.xml"))
        >>> 
        >>> all_texts_found = []
        >>> for xml_file in xml_files:
        ...     node = 提取xml中的视频节点(xml_file)
        ...     if node:
        ...         texts = 提取节点内所有文字(node)
        ...         text_values = [v for t, v in texts]
        ...         all_texts_found.append({
        ...             'file': xml_file.name,
        ...             'text_count': len(texts),
        ...             'has_author': any('@' in v for v in text_values),
        ...             'has_numbers': any(v.isdigit() for v in text_values if v)
        ...         })
        >>> 
        >>> len(all_texts_found) == len(xml_files)
        True
        >>> all(t['text_count'] > 0 for t in all_texts_found)
        True
        >>> all(t['has_author'] for t in all_texts_found)
        True
    """
    results = []
    
    def _递归提取(n: ET.Element):
        # 提取 text 属性
        text = n.get('text', '').strip()
        if text:
            results.append(('text', text))
        
        # 提取 content-desc 属性
        content_desc = n.get('content-desc', '').strip()
        if content_desc:
            results.append(('content-desc', content_desc))
        
        # 递归处理子节点
        for child in n:
            _递归提取(child)
    
    _递归提取(node)
    return results


def 格式化视频信息(xml_source: Union[ET.ElementTree, ET.Element, str, Path]) -> str:
    """
    格式化输出抖音视频页面的信息
    
    该函数首先提取视频容器节点，然后从节点中提取关键信息并格式化为易读的文本。
    不依赖临时资源ID，而是使用 content-desc、位置等稳定特征。
    
    Args:
        xml_source: XML 源，可以是：
            - xml.etree.ElementTree.ElementTree 对象
            - xml.etree.ElementTree.Element 对象
            - XML 文件路径（str 或 Path）
    
    Returns:
        格式化后的视频信息字符串
    
    Examples:
        >>> # 测试所有 XML 文件的格式化输出
        >>> current_dir = Path(__file__).parent
        >>> xml_dir = current_dir / "ut" / "xmls"
        >>> xml_files = list(xml_dir.glob("*.xml"))
        >>> 
        >>> all_outputs = []
        >>> for xml_file in xml_files:
        ...     output = 格式化视频信息(xml_file)
        ...     all_outputs.append({
        ...         'file': xml_file.name,
        ...         'has_video_info': '视频信息' in output,
        ...         'has_author': '作者昵称:' in output,
        ...         'has_interaction': '互动数据' in output,
        ...         'has_content': '视频文案:' in output and '音乐信息:' in output,
        ...     })
        >>> 
        >>> len(all_outputs) == len(xml_files)
        True
        >>> all(o['has_video_info'] for o in all_outputs)
        True
        >>> all(o['has_author'] for o in all_outputs)
        True
        >>> all(o['has_interaction'] for o in all_outputs)
        True
        >>> all(o['has_content'] for o in all_outputs)
        True
    """
    # 提取视频容器节点
    video_node = 提取xml中的视频节点(xml_source)
    
    if video_node is None:
        return "未找到视频容器节点"
    
    # 提取各项信息
    info = {
        '作者': _提取作者昵称(video_node),
        '文案': _提取视频文案(video_node),
        '音乐': _提取音乐信息(video_node),
        '点赞': _提取点赞数(video_node),
        '评论': _提取评论数(video_node),
        '收藏': _提取收藏数(video_node),
        '分享': _提取分享数(video_node),
    }
    
    # 格式化输出
    lines = [
        "📱 视频信息",
        "",
        f"作者昵称: {info['作者']}",
        f"视频文案: {info['文案']}",
        f"音乐信息: {info['音乐']}",
        "",
        "📊 互动数据",
        "",
        f"👍 点赞数: {info['点赞']}",
        f"💬 评论数: {info['评论']}",
        f"⭐ 收藏数: {info['收藏']}",
        f"↗️ 分享数: {info['分享']}",
    ]
    
    return '\n'.join(lines)


def _提取作者昵称(node: ET.Element) -> str:
    """
    从视频/直播节点中提取作者/主播昵称
    
    策略：
    1. 优先查找 text 以 "@" 开头的节点（最稳定，通常是 com.ss.android.ugc.aweme:id/title）
    2. 从 content-desc 中提取，但排除音乐相关的节点
    3. 查找 content-desc 包含 "直播中" 的节点
    """
    # 策略1：优先使用 text 属性（作者昵称通常有直接的 text）
    for child in node.iter():
        text = child.get('text', '').strip()
        # 以 @ 开头且不包含"创作的原声"（音乐）
        if text.startswith('@') and '创作的原声' not in text:
            return text
    
    # 策略2：从 content-desc 中提取，但排除音乐相关
    for child in node.iter():
        content_desc = child.get('content-desc', '')
        
        # 跳过音乐相关的节点
        if '音乐' in content_desc or '创作的原声' in content_desc:
            continue
        
        # 匹配 "@用户名，按钮" 或 "@用户名直播中，按钮" 格式
        match = re.search(r'@([^，]+)', content_desc)
        if match and '按钮' in content_desc:
            nickname = match.group(1).replace('直播中', '').strip()
            if nickname:
                return f"@{nickname}"
    
    return '未知'


def _提取视频文案(node: ET.Element) -> str:
    """
    从视频/直播节点中提取视频文案/直播标题
    
    策略：
    1. 查找包含话题标签(#)的 text
    2. 查找较长的文本（文案通常较长）
    3. 直播页面查找 "点击进入直播间"
    """
    candidates = []
    
    for child in node.iter():
        text = child.get('text', '').strip()
        if not text or len(text) < 2:
            continue
        
        # 优先级1：包含话题标签的文本（肯定是文案）
        if '#' in text:
            return text
        
        # 优先级2：包含 "点击进入直播间"（直播）
        if '直播间' in text:
            return f"[直播间] {text}"
        
        # 收集候选（长度在10-100之间的文本）
        if 10 <= len(text) <= 100:
            candidates.append(text)
    
    # 返回最长的候选
    if candidates:
        return max(candidates, key=len)
    
    return '无'


def _提取音乐信息(node: ET.Element) -> str:
    """
    从视频/直播节点中提取音乐信息/直播状态
    
    策略：
    1. 查找 content-desc 包含 "音乐" 或 "创作的原声" 的节点
    2. 查找 content-desc 包含 "直播中" 的节点
    """
    for child in node.iter():
        content_desc = child.get('content-desc', '')
        
        # 匹配音乐信息
        match = re.search(r'音乐，(.+?)，按钮', content_desc)
        if match:
            return match.group(1)
        
        # 备选音乐格式
        if '创作的原声' in content_desc:
            return content_desc.replace('音乐，', '').replace('，按钮', '')
        
        # 直播状态
        if '直播中，按钮' in content_desc:
            return '📺 直播中'
    
    return '未知'


def _提取点赞数(node: ET.Element) -> str:
    """
    提取点赞数
    
    策略：
    1. 查找 content-desc 包含 "喜欢" 或 "点赞" 的节点
    2. 从该节点或其子节点提取数字
    """
    return _从描述中提取数字(node, r'(喜欢|点赞)', r'(\d+)')


def _提取评论数(node: ET.Element) -> str:
    """
    提取评论数
    
    策略：
    1. 查找 content-desc 包含 "评论" 的节点
    2. 从该节点或其子节点提取数字
    """
    return _从描述中提取数字(node, r'评论', r'(\d+)')


def _提取收藏数(node: ET.Element) -> str:
    """
    提取收藏数
    
    策略：
    1. 查找 content-desc 包含 "收藏" 的节点
    2. 从该节点或其子节点提取数字
    """
    return _从描述中提取数字(node, r'收藏', r'(\d+)')


def _提取分享数(node: ET.Element) -> str:
    """
    提取分享数
    
    策略：
    1. 查找 content-desc 包含 "分享" 的节点
    2. 从该节点或其子节点提取数字
    """
    return _从描述中提取数字(node, r'分享', r'(\d+)')


def _从描述中提取数字(node: ET.Element, desc_pattern: str, num_pattern: str) -> str:
    """
    从 content-desc 匹配的节点中提取数字
    
    策略：
    1. 先找 content-desc 包含指定描述的节点
    2. 从该节点的 text 提取数字
    3. 从子节点的 text 提取数字
    4. 从 content-desc 本身提取数字
    """
    for child in node.iter():
        content_desc = child.get('content-desc', '')
        
        if re.search(desc_pattern, content_desc):
            # 尝试从当前节点的 text 提取
            text = child.get('text', '').strip()
            if text.isdigit():
                return text
            
            # 尝试从子节点的 text 提取
            for subchild in child:
                subtext = subchild.get('text', '').strip()
                if subtext.isdigit():
                    return subtext
            
            # 尝试从 content-desc 提取数字
            match = re.search(num_pattern, content_desc)
            if match:
                return match.group(1)
    
    return '0'


def 提取结构化数据(xml_source: Union[ET.ElementTree, ET.Element, str, Path]) -> dict:
    """
    从 XML 中提取结构化的视频/直播信息
    
    该函数提取关键信息并返回字典格式，包含类型识别（视频/直播/其他）。
    
    Args:
        xml_source: XML 源，可以是：
            - xml.etree.ElementTree.ElementTree 对象
            - xml.etree.ElementTree.Element 对象
            - XML 文件路径（str 或 Path）
    
    Returns:
        包含视频/直播信息的字典，字段包括：
        - 作者: 作者/主播昵称
        - 文案: 视频文案/直播标题
        - 音乐: 音乐信息/直播状态
        - 点赞: 点赞数
        - 评论: 评论数
        - 收藏: 收藏数
        - 分享: 分享数
        - 类型: "视频" / "直播" / "其他"
    
    Examples:
        >>> # 测试：对比所有 XML 文件的提取结果与对应的 JSON 基准文件
        >>> # 注意：运行测试前需要先执行 批量导出JSON基准文件() 生成基准文件
        >>> current_dir = Path(__file__).parent
        >>> xml_dir = current_dir / "ut" / "xmls"
        >>> xml_files = list(xml_dir.glob("*.xml"))
        >>> 
        >>> # 筛选出有对应 JSON 基准文件的 XML
        >>> test_files = [(xml, xml.with_suffix('.json')) for xml in xml_files if xml.with_suffix('.json').exists()]
        >>> len(test_files) > 0  # 确保至少有一个测试文件
        True
        >>> 
        >>> mismatch_list = []
        >>> for xml_file, json_file in test_files:
        ...     # 提取当前数据
        ...     actual_data = 提取结构化数据(xml_file)
        ...     # 读取基准数据
        ...     with open(json_file, 'r', encoding='utf-8') as f:
        ...         expected_data = json.load(f)
        ...     # 对比
        ...     if actual_data != expected_data:
        ...         mismatch_list.append({
        ...             'file': xml_file.name,
        ...             'expected': expected_data,
        ...             'actual': actual_data
        ...         })
        >>> 
        >>> # 验证没有不匹配的情况
        >>> len(mismatch_list)
        0
    """
    # 提取视频容器节点
    video_node = 提取xml中的视频节点(xml_source)
    
    if video_node is None:
        return {
            '作者': '未知',
            '文案': '无',
            '音乐': '未知',
            '点赞': '0',
            '评论': '0',
            '收藏': '0',
            '分享': '0',
            '类型': '其他'
        }
    
    # 提取各项信息
    info = {
        '作者': _提取作者昵称(video_node),
        '文案': _提取视频文案(video_node),
        '音乐': _提取音乐信息(video_node),
        '点赞': _提取点赞数(video_node),
        '评论': _提取评论数(video_node),
        '收藏': _提取收藏数(video_node),
        '分享': _提取分享数(video_node),
    }
    
    # 识别类型
    info['类型'] = _识别内容类型(video_node, info)
    
    return info


def _识别内容类型(node: ET.Element, info: dict) -> str:
    """
    识别内容类型（视频/直播/其他）
    
    策略：
    1. 检查音乐信息是否为 "📺 直播中"
    2. 检查文案是否包含 "[直播间]"
    3. 检查是否有直播相关的 content-desc
    """
    # 检查音乐信息
    if info.get('音乐') == '📺 直播中':
        return '直播'
    
    # 检查文案
    if '[直播间]' in info.get('文案', ''):
        return '直播'
    
    # 检查节点中的直播标识
    for child in node.iter():
        content_desc = child.get('content-desc', '')
        if '直播中' in content_desc:
            return '直播'
    
    # 默认为视频
    return '视频'


def 批量导出JSON基准文件(ut_xmls_dir: Union[str, Path] = None, force: bool = False) -> dict:
    """
    批量将 XML 文件的结构化数据导出为 JSON 基准文件
    
    【重要提醒 - 给后续 Code Agent】
    ========================================
    1. 本函数生成的 JSON 文件是单元测试的基准文件，一旦生成请勿删除！
    2. JSON 文件用于验证 "提取结构化数据" 函数的输出是否正确
    3. 如需修正数据，请手动编辑 JSON 文件，而非删除重新生成
    4. 这些文件是测试套件的一部分，删除会导致测试失败
    ========================================
    
    导出规则：
    - 每个 XML 文件会生成一个同名的 JSON 文件（如 20260225_164300.xml → 20260225_164300.json）
    - 如果 JSON 文件已存在，默认会跳过（不覆盖），除非设置 force=True
    - 只处理新增的 XML 文件（增量导出）
    
    Args:
        ut_xmls_dir: XML 文件目录路径，默认为当前文件所在目录下的 ut/xmls
        force: 是否强制覆盖已存在的 JSON 文件，默认为 False（不建议使用）
    
    Returns:
        导出结果字典，包含以下信息：
        - exported: 新导出的文件列表
        - skipped: 跳过的文件列表（已存在）
        - total: 处理的 XML 文件总数
    """
    if ut_xmls_dir is None:
        ut_xmls_dir = Path(__file__).parent / "ut" / "xmls"
    else:
        ut_xmls_dir = Path(ut_xmls_dir)
    
    xml_files = sorted(ut_xmls_dir.glob("*.xml"))
    
    exported = []
    skipped = []
    
    for xml_file in xml_files:
        json_file = xml_file.with_suffix('.json')
        
        # 如果文件已存在且未设置 force，则跳过
        if json_file.exists() and not force:
            skipped.append(json_file.name)
            continue
        
        # 提取结构化数据
        data = 提取结构化数据(xml_file)
        
        # 写入 JSON 文件
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        exported.append(json_file.name)
    
    return {
        'exported': exported,
        'skipped': skipped,
        'total': len(xml_files)
    }


def 批量格式化打印(ut_xmls_dir: Union[str, Path] = None) -> str:
    """
    批量解析并格式化打印所有 XML 文件的信息
    
    以列表方式输出所有 XML 文件的解析结果（使用结构化数据）。
    
    Args:
        ut_xmls_dir: XML 文件目录路径，默认为当前文件所在目录下的 ut/xmls
    
    Returns:
        格式化后的列表字符串
    """
    if ut_xmls_dir is None:
        ut_xmls_dir = Path(__file__).parent / "ut" / "xmls"
    else:
        ut_xmls_dir = Path(ut_xmls_dir)
    
    xml_files = sorted(ut_xmls_dir.glob("*.xml"))
    
    if not xml_files:
        return "未找到 XML 文件"
    
    lines = []
    for i, xml_file in enumerate(xml_files, 1):
        # 使用结构化数据提取函数
        data = 提取结构化数据(xml_file)
        
        # 格式化输出
        lines.append(f"文件 {i}: {xml_file.name}")
        lines.append("")
        lines.append(f"  • 作者: {data['作者']}")
        lines.append(f"  • 文案: {data['文案']}")
        lines.append(f"  • 类型: {data['类型']}")
        lines.append(f"  • 互动: {data['点赞']}赞 / {data['评论']}评论 / {data['收藏']}收藏 / {data['分享']}分享")
        lines.append("")
    
    return '\n'.join(lines)


if __name__ == "__main__":
    import doctest
    
    # 运行 doctest，verbose=True 显示详细测试信息
    results = doctest.testmod(verbose=True)
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"尝试运行测试数: {results.attempted}")
    print(f"失败测试数: {results.failed}")
    
    if results.failed == 0:
        print("✓ 所有测试通过！")
        print("\n" + "=" * 60)
        print("批量打印示例")
        print("=" * 60)
        print(批量格式化打印())
    else:
        print("✗ 部分测试失败")
        exit(1)
