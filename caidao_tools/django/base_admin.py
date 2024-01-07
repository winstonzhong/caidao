'''
Created on 2022年7月24日

@author: lenovo
'''
from django.contrib import admin

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
