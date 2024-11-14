'''
Created on 2022年7月24日

@author: lenovo
'''
import os
from django.contrib import admin
from django.utils.safestring import mark_safe
from tool_file import get_suffix

def to_img_html(fpath, width=100):
    if fpath.name:
        return mark_safe(f'''<img src="{fpath.url}" width={width}/>''')

def to_video_html(fpath, width=100):
    if fpath.name:
        return  mark_safe(f'''<video controls  playsinline="" style="display: block; max-height: 100%; max-width: 100%;" width={width};>
        <source src="{fpath.url}" type="video/{get_suffix(fpath.name).lower()}">
        </video>''')
    
def to_media_html(fpath, width=200):
    if fpath.name:
        if get_suffix(fpath.name).lower() in ('mp4', 'avi'):
        # if fpath.name.lower().endswith('.mp4'):
            return to_video_html(fpath, width)
        return to_img_html(fpath, width)

class BaseAdmin(admin.ModelAdmin):
    def list_display_filter(self, x):
        l1 = self.list_display_exclude if hasattr(self, 'list_display_exclude') else tuple()
        l1 = l1 or tuple()
        return x not in l1
    
    def get_display_fields(self):
        if hasattr(self, 'list_display_replace'):
            list_display_replace = self.list_display_replace
        else:
            list_display_replace = {}
        
        
        for x in map(lambda x:x.name, getattr(self.model, "_meta").fields):
            yield list_display_replace.get(x,x)
        
        if hasattr(self, 'list_display_include') and self.list_display_include:
            for x in self.list_display_include:
                yield list_display_replace.get(x,x)
    
    def get_list_display(self, request):
        if hasattr(self, 'list_display') and self.list_display[0] != '__str__':
            return self.list_display
        return list(filter(self.list_display_filter, self.get_display_fields()))

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def get_queryset(self, request):
        self.request = request
        return super().get_queryset(request)

    class Media:
        js = []

        # 示例: {'all': ['xxx']}
        css = {}
        rel_js_path = 'static/js/htmx.min.js'
        if os.path.lexists(rel_js_path) or os.path.lexists(f'../{rel_js_path}'):
            js.append(f'/{rel_js_path}')


class CodeBaseAdmin(BaseAdmin):
    class Media:
        additional_js_list = [
            '/static/js/codemirror/lib/codemirror.js',
            '/static/js/codemirror/addon/display/fullscreen.js',
            '/static/js/codemirror/addon/edit/matchbrackets.js',
            '/static/js/codemirror/addon/selection/active-line.js',
            '/static/js/codemirror/mode/python/python.js',
            '/static/js/utils.js',
        ]
        # BaseAdmin.Media.js += additional_js_list
    
        additional_css_dict = {
            'all': ['/static/css/codemirror/lib/codemirror.css',
                    '/static/css/codemirror/addon/display/fullscreen.css',
                    '/static/css/codemirror/theme/monokai.css',
                    '/static/css/codemirror/theme/blackboard.css',
                    '/static/css/default.min.css',
                    ]
        }

        js = ['/static/js/htmx.min.js', '/static/js/highlight.min.js'] + additional_js_list
        css = additional_css_dict
