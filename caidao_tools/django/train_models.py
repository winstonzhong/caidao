'''
Created on 2024 Mar 4

@author: Winston
'''
import base64
import hashlib

import cv2
from django.db import models
from django.db.models.aggregates import Sum
from django.utils.functional import cached_property
import numpy
import torch

from helper_trainer import resize, NeuralNetwork
from caidao_tools.django.abstract import BaseModel




class BaseTrain(BaseModel):
    MIN_PROB = 0.9
    bin = models.BinaryField()
    prob = models.FloatField(null=True, blank=True)
    training = models.BooleanField(default=False, verbose_name='训练记录')
    key = models.CharField(max_length=64, null=True, blank=True)
    weight = models.PositiveSmallIntegerField(default=1) 
    
    class Meta:
        abstract = True
        
    @classmethod
    def get_total_training_num(cls):
        q = cls.objects.filter(training=1)
        return q.aggregate(Sum('weight')).get('weight__sum')

    @classmethod
    def get_training_records(cls, *a, **k):
        for x in cls.objects.filter(training=1):
            for _ in range(x.weight):
                yield x

    @classmethod
    def get_resizer(cls):
        return resize
    
    @classmethod
    def transform(cls, x):
        return cls.get_resizer()(x).type(torch.float)

    @classmethod
    def get_tensor(cls, image):
        image = image.reshape(1, *image.shape)
        return torch.tensor(image)
        
    @property
    def base64(self):
        return base64.b64encode(self.bin).decode()

    @cached_property
    def src_base64(self):
        return 'data:image/png;base64,' + self.base64
    
    @property
    def img(self):
        img = numpy.frombuffer(self.bin, numpy.uint8)
        return cv2.imdecode(img, cv2.IMREAD_ANYCOLOR)
    
    @property
    def tensor(self):
        return self.get_tensor(self.img)
    
    @property
    def tensor_transformed(self):
        return self.transform(self.tensor)
    
    @classmethod
    def get_tensor_transformed(cls, img):
        return cls.transform(cls.get_tensor(img))
    
    @property
    def X(self):
        X = [self.tensor_transformed]
        return torch.stack(X).type(torch.float)


    @classmethod
    def get_X(cls, imgs):
        l = []
        for x in imgs:
            # x = x.astype(numpy.uint8) * 255
            l.append(cls.get_resizer()(torch.tensor(x.reshape((1,*x.shape)))))
        return torch.stack(l).type(torch.float) if l else None
    
    @classmethod
    def get_X_all(cls, *a, **k):
        q = cls.objects.filter(**cls.get_filters(**k))
        ids = []
        X = []
        for x in q:
            ids.append(x.id)
            X.append(x.tensor_transformed)
            # X = [x.tensor_transformed for x in q]
        return torch.stack(X).type(torch.float), ids
    
    @classmethod
    def get_key(cls, img):
        return hashlib.sha256(img.tobytes()).hexdigest()
    
    @classmethod
    def get_model(cls):
        if not hasattr(cls, '_model'):
            print('loading number model...')
            m = NeuralNetwork(len(cls.TYPE_DN))
            m.load_state_dict(torch.load(f'{cls.__name__.lower()}.pth'))
            m.eval()
            cls._model = m
        return cls._model

    @classmethod
    def predict_X(cls, X):
        pred = cls.get_model()(X)
        labels = pred.argmax(1).tolist()
        return labels
    
    @classmethod
    def predict_imgs(cls, imgs):
        return cls.predict_X(cls.get_X(imgs))
    
    @classmethod
    def convert_labels_to_int(cls, labels, keep_str=False):
        s = ''.join(map(lambda x:cls.TYPE_DN[x][1], labels)) 
        return int(s) if not keep_str else s
    
    def predict(self):
        return self.predict_X(self.X)
    
    @property
    def model(self):
        return self.get_model()    
    


# class AbstractModel(BaseModel):
#     update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
#     create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
#
#     class Meta:
#         abstract = True
    