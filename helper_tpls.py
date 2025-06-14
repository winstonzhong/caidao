from jinja2 import Environment, FileSystemLoader, DictLoader
from pathlib import Path


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
        <title>{{ title }}</title>
    </head>
    <body>
        <h1>{{ title }}</h1>
        <p>{{ content }}</p>
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