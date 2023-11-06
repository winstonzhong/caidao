'''
Created on 2023 Oct 25

@author: Winston
'''
import json
import os

from django.db import models
from django.utils.functional import cached_property

from caidao_tools.django.abstract import StatusModel, FullTextField, BaseModel,\
    ABNORMAL_RECORD
from tool_gzip import gzip_decompress
from tool_file import get_dir_key, has_file


class AbstractWord(BaseModel):
    MAX_LEN_EN = 50
    MAX_LEN_CN = 100
    en = models.CharField(max_length=MAX_LEN_EN)
    cn = models.CharField(max_length=MAX_LEN_CN)
    
    

    class Meta:
        abstract = True

class AbstractTemplateModel(StatusModel):
    mid = models.PositiveBigIntegerField(verbose_name='csite模型id')
    vid = models.PositiveBigIntegerField(verbose_name='csite模型vid')
    tid = models.PositiveBigIntegerField()
    bin = models.BinaryField()
    meta_info = FullTextField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def tag_tpl(self):
        if self.suffix == 'mp4':
            return '''<video autoplay="" loop="" playsinline="" src="{0}" style="display: block; max-height: 100%; max-width: 100%;"><source src="https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/1bc3f02d-bf6f-4687-a955-3e0aac83e5cc/transcode=true,width=450/lv_0_20231022221025.webm" type="video/webm"><source src="https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/1bc3f02d-bf6f-4687-a955-3e0aac83e5cc/transcode=true,width=450/lv_0_20231022221025.mp4" type="video/mp4"></video>'''
        return '<img src="{0}" />'
         
    @property
    def tag_media(self):
        return self.tag_tpl.format(self.url)
    
    @cached_property
    def fname(self):
        return "%s.%s" % (self.uuid, self.suffix)

    @cached_property
    def dir_middle(self):
        return get_dir_key(self.fname)
    
    @cached_property
    def fpath_img(self):
        return os.path.join(self.CACHE_DIR, self.dir_middle, self.fname)


    def has_image(self):
        return has_file(self.fpath_img)


    @cached_property
    def uuid(self):
        return self.json.get('url') or None

    @cached_property
    def suffix(self):
        return self.json.get('mimeType','').split('/')[-1]


    @property
    def url_site(self):
        return 'https://civitai.com/models/{0}?modelVersionId={1}'.format(self.mid, self.vid)

    @cached_property
    def url(self):
        return 'https://btmy.j1.sale:8090/media/{0}/{1}'.format(self.dir_middle, self.fname)

    @cached_property
    def json(self):
        try:
            return json.loads(gzip_decompress(self.bin).decode('utf8'))
        except:
            self.status = ABNORMAL_RECORD
            self.save_safe()
            return {}
    
    @property
    def prompt(self):
        return self.json.get('meta').get('prompt')
    
    @property
    def negativePrompt(self):
        return self.json.get('meta').get('negativePrompt')
    
    
    @property
    def names_model(self):
        for x in self.json.get('meta').get('resources'):
            yield x.get('name')
        
    
    
    

