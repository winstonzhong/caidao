from django.contrib import admin

# Register your models here.
from django.utils.safestring import mark_safe
from caidao_tools.django.base_admin import BaseAdmin

from mini_program.models import *


class MsgAdmin(BaseAdmin):
    search_fields = ['from_user_name', 'to_user_name', 'text']
    list_display = ['id', 'from_user_name', 'to_user_name', 'text', 'img', 'reply']
    list_editable = ('reply',)
    list_filter = ('from_user_name',)

    def img(self, obj):
        if obj.pic_url:
            return mark_safe('<img src="{0}" />'.format(obj.pic_url))
        return ''
    img.short_description = '图像'

    def save_model(self, request, obj, form, change):

        if change and obj.reply:
            data = {
                "from_user_name": obj.to_user_name,
                "to_user_name": obj.from_user_name,
                "parent_id": obj.id,
                "text": obj.reply
            }
            Msg.objects.create(**data)
            obj.reply = ''
        return super().save_model(request, obj, form, change)


admin.site.register(Msg, MsgAdmin)