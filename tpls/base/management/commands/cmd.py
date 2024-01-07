# encoding: utf-8
'''
Created on 2015年8月14日

@author: root
'''

from django.core.management.base import BaseCommand



class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--test', action='store_true', default=False)
        parser.add_argument('--name', nargs = "?", default='', type=str)


    def handle(self, *args, **options):
        if options.get('test'):
            print('testing..')
