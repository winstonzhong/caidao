'''
Created on 2024 Mar 4

@author: Winston
'''
import base64
import hashlib

from django.db import models
from django.db.models.aggregates import Sum, Count
from django.db.models.query_utils import Q
from django.utils.functional import cached_property
import numpy
import torch
from torchvision import transforms

from caidao_tools.django.abstract import BaseModel
from helper_cmd import CmdProgress
from tool_img import bin2img


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
    def get_next_label(cls):
        obj = cls.objects.filter().order_by('label').last()
        return obj.label + 1 if obj is not None else 1

    @classmethod
    def get_fpath_pth(cls):
        return cls.fpath_pth


    @classmethod
    def batch_update(cls, l):
        objs = []
        cp = CmdProgress(len(l))
        field_names = [x for x in l[0].keys() if x !='id']
        for d in l:
            obj = cls.objects.get(id=d.get('id'))
            for name in field_names:
                setattr(obj, name, d.get(name))
            objs.append(obj)
            cp.update()
        cls.objects.bulk_update(objs, field_names)
        
    @classmethod
    def get_label_ids(cls, for_training):
        q = cls.objects.filter() if for_training else cls.objects.exclude(pred_label_id=None) 
        l = q.values('label').distinct()
        return list(map(lambda x:x.get('label'), l))
        # if refresh or not hasattr(cls, '_get_label_ids'):
        #     l = cls.objects.filter().values('label').distinct()
        #     l = list(map(lambda x:x.get('label'), l))
        #     cls._get_label_ids = l
        # return cls._get_label_ids

    @classmethod
    def get_labels(cls, for_training):
        l = cls.get_label_ids(for_training=for_training)
        return tuple((x, str(x)) for x in l)
    
    @classmethod
    def get_curent_batch_number(cls):
        obj = cls.objects.filter().order_by('batch_number').last()
        return obj.batch_number if obj is not None else 0 
        
    @classmethod
    def get_next_batch_number(cls):
        obj = cls.objects.filter().order_by('batch_number').last()
        return obj.batch_number + 1 if obj is not None else 0


    @property
    def label_id(self):
        return self.label

    @classmethod
    def ge_nn_model(cls):
        if not hasattr(cls, '_nn_model'):
            print('loading model...')
            cls._nn_model = cls.get_nn().load_model()
        return cls._nn_model

    @classmethod
    def get_training_distribution(cls):
        q = cls.objects.filter(training=1)
        return q.values('label').annotate(count=Count('label'))

    @classmethod
    def get_max_training_label_num(cls):
        l = list(cls.get_training_distribution())
        a = map(lambda x:x.get('count'), l)
        return  max(a), len(l)

    
    @classmethod
    def get_total_training_num(cls):
        m, n = cls.get_max_training_label_num()
        return m * n


    @classmethod
    def get_training_records_num(cls, label, num):
        i = 0
        l = list(cls.objects.filter(training=1, label=label))
        while i < num:
            for x in l:
                if i < num:
                    yield x
                    i += 1
                else:
                    break

        
    @classmethod
    def get_training_records(cls, *a, **k):
        for x in cls.objects.filter(Q(training=1) | Q(label__gt=0)):
            for _ in range(x.weight):
                yield x

    @classmethod
    def get_testing_records(cls, *a, **k):
        for x in cls.objects.filter(Q(training=0) | Q(label__gt=0)):
            for _ in range(x.weight_test):
                yield x

    @classmethod
    def get_learning_rate(cls):
        return 1e-3
    
    @classmethod
    def get_batch_size(cls):
        return 64
    
    @classmethod
    def get_input_shape(cls):
        return (64, 64)
    
    @classmethod
    def get_resizer(cls):
        if cls.resizer is None:
            cls.resizer = transforms.Resize(cls.get_input_shape(),antialias=True) 
        return cls.resizer

    # @classmethod
    # def get_resizer(cls):
    #     return resize
    
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
    
    # @property
    # def img(self):
    #     img = numpy.frombuffer(self.bin, numpy.uint8)
    #     return cv2.imdecode(img, cv2.IMREAD_ANYCOLOR)

    @cached_property
    def img(self):
        return bin2img(self.bin)

    
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
        print('loading all X...')
        q = cls.objects.filter(**cls.get_filters(**k))
        ids = []
        X = []
        cp = CmdProgress(q.count())
        for x in q:
            ids.append(x.id)
            X.append(x.tensor_transformed)
            cp.update()
            # X = [x.tensor_transformed for x in q]
        return torch.stack(X).type(torch.float), ids
    
    @classmethod
    def get_X_by_list(cls, l):
        # X = []
        # for x in l:
        #     X.append(x.tensor_transformed)
        X = [x.tensor_transformed for x in l]
        return torch.stack(X).type(torch.float)

    @classmethod
    def get_nn(cls):
        raise NotImplementedError

    @classmethod
    def test_all(cls):
        m = cls.get_model()
        X, ids = cls.get_X_all()
        pred = m(X)
        probs = torch.softmax(pred, dim=1)
        # p, _ = probs.max(axis=1)
        p, l = probs.max(axis=1)
        cp = CmdProgress(len(ids))
        objs = []
        print('testing...')
        for i in range(len(l)):
            o = cls.objects.get(id=ids[i])
            o.pred_label_id = int(l[i])
            o.pred_label_name = m.get_label_name(int(l[i]))
            o.prob = float(p[i])
            objs.append(o)
            cp.update()
        cls.objects.bulk_update(objs, ('pred_label_id', 'pred_label_name', 'prob'))

    
    @classmethod
    def get_key(cls, img):
        return hashlib.sha256(img.tobytes()).hexdigest()
    
    @classmethod
    def get_model(cls, refresh=False, for_training=False):
        if not hasattr(cls, '_model') or cls._model is None or refresh:
            print(f'loading {cls} model...')
            m = cls.get_nn(for_training)
            m.load_state_dict(torch.load(cls.get_fpath_pth()))
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
    
    def predict_probs(self):
        return torch.softmax(self.model(self.X), dim=1)
    
    @property
    def model(self):
        return self.get_model()    
    


# class AbstractModel(BaseModel):
#     update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
#     create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
#
#     class Meta:
#         abstract = True
    