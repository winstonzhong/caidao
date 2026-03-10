# encoding: utf-8
'''
Created on 2015年8月14日

@author: root
'''
import os

from django.core.management.base import BaseCommand



class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--test', action='store_true', default=False)
        parser.add_argument('--name', nargs = "?", default='', type=str)
        parser.add_argument('--DY_FORCE_MATCH_FRIEND_VIDEO', action='store_true', default=False,
                            help='强制朋友视频也进行匹配检查，设置环境变量 DY_FORCE_MATCH_FRIEND_VIDEO=1')


    def handle(self, *args, **options):
        # 设置环境变量：强制朋友视频匹配
        if options.get('DY_FORCE_MATCH_FRIEND_VIDEO'):
            os.environ['DY_FORCE_MATCH_FRIEND_VIDEO'] = '1'
            print('[环境变量] DY_FORCE_MATCH_FRIEND_VIDEO 已设置为 1，朋友视频将强制进行匹配检查')
        
        if options.get('test'):
            print('testing..')
