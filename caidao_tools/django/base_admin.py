'''
Created on 2022年7月24日

@author: lenovo
'''
from django.contrib import admin

class BaseAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        if hasattr(self, 'list_display'):
            return self.list_display
        return list(map(lambda x:x.name, getattr(self.model, "_meta").fields))

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions
