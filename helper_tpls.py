from jinja2 import Environment, FileSystemLoader, DictLoader, TemplateError
from pathlib import Path

import requests

def render_template_file_to_string(template_path, context):
    """
    使用 Jinja2 渲染模板文件为字符串

    :param template_path: 模板文件的路径
    :param context: 上下文字典
    :return: 渲染后的字符串
    """
    # 创建一个模板环境，指定模板文件所在的目录
    template_path = Path(template_path).resolve()
    template_dir = template_path.parent
    # template_dir = "/".join(template_path.split("/")[:-1])  # 获取模板文件所在目录
    env = Environment(loader=FileSystemLoader(template_dir))

    # 加载模板文件
    # template_name = template_path.split("/")[-1]  # 获取模板文件名
    template_name = template_path.name
    template = env.get_template(template_name)

    # 渲染模板
    return template.render(context)


def render_template_url_to_string(url, timeout=10, headers=None, **context):
    """
    通过URL获取模板内容，使用Jinja2渲染为字符串

    :param url: 模板内容的URL地址
    :param context: Jinja2渲染用的上下文字典
    :param timeout: 请求URL的超时时间（秒），默认10秒
    :param headers: 请求头字典（可选），例如 {"User-Agent": "Mozilla/5.0"}
    :return: 渲染后的字符串
    :raises requests.RequestException: URL请求失败（网络错误/HTTP错误）时抛出
    :raises TemplateError: Jinja2模板渲染失败时抛出
    :raises RuntimeError: 其他通用错误（如内容为空）时抛出
    """
    # 初始化默认请求头
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    if headers:
        default_headers.update(headers)

    try:
        # 发送GET请求拉取模板内容
        response = requests.get(
            url=url,
            headers=default_headers,
            timeout=timeout,
            verify=True  # 生产环境建议开启SSL验证，如需关闭可设为False（不推荐）
        )
        # 检查HTTP状态码（非2xx会抛出HTTPError）
        response.raise_for_status()

        # 获取模板内容（自动处理编码，优先从响应头推断）
        template_content = response.text
        if not template_content.strip():
            raise RuntimeError(f"URL {url} 返回的模板内容为空")

        # 复用原有渲染逻辑
        return render_template_string_to_string(template_content, context)

    # 捕获所有requests相关异常（网络错误、超时、HTTP错误等）
    except requests.RequestException as e:
        raise requests.RequestException(
            f"获取URL模板内容失败（URL: {url}）: {str(e)}"
        ) from e
    # 捕获模板渲染异常
    except TemplateError as e:
        raise TemplateError(
            f"渲染URL模板失败（URL: {url}）: {str(e)}"
        ) from e
    # 捕获其他自定义错误
    except RuntimeError as e:
        raise RuntimeError(f"处理URL模板失败: {str(e)}") from e

def render_template_string_to_string(template_content, context):
    """
    使用 Jinja2 渲染模板字符串为字符串

    :param template_content: 模板字符串内容
    :param context: 上下文字典
    :return: 渲染后的字符串
    """
    # 创建一个模板环境，使用字典加载器
    env = Environment(loader=DictLoader({"template": template_content}))

    # 加载模板
    template = env.get_template("template")

    # 渲染模板
    return template.render(context)

if __name__ == "__main__":
    context = {
        'title': 'Hello, World!',
        'content': 'This is a test template.',
        'items': ['Item 1', 'Item 2', 'Item 3']
    }

    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{title}}</title>
    </head>
    <body>
        <h1>{{ title }}</h1>
        <p>{{content}}</p>
        <ul>
            {% for item in items %}
                <li>{{ item }}</li>
            {% endfor %}
        </ul>
    </body>
    </html>
    """

    rendered_string = render_template_string_to_string(template, context)
    print(rendered_string)