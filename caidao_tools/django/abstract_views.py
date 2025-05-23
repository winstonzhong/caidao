import json
from rest_framework.views import APIView
from django.http.response import JsonResponse

# Create your views here.


class 基础任务视图(APIView):
    @property
    def model(self):
        raise NotImplementedError

    def get(self, request):
        d = self.model.筛选出数据库字段(request.GET)
        for k, v in d.items():
            if v in ('False', 'True'):
                d[k] = eval(v)
        obj = self.model.objects.filter(**d).first()
        
        obj = self.after_get(request, obj)

        if obj is not None:
            return JsonResponse(obj.json)
        else:
            return JsonResponse({})

    def after_get(self, request, obj):
        return obj
    
    def after_post(self, request, obj):
        pass
    
    # def get_post_dict(self, request):
    #     print(request.POST)
    #     # d = len(request.POST)
    #     # if not d:
    #         # d = json.loads(request.body)
    #     # return d        
    #     return json.loads(request.body)
    
    def post(self, request):
        # d = self.get_post_dict(request)
        d = request.POST.dict()
        # print("==============>", d)
        pk_name = d.get("pk_name")
        
        pk_value = d.get("pk_value")

        assert pk_name and pk_value, "pk_name or pk_value is None"

        d = self.model.筛选出数据库字段(d)

        q = self.model.objects.filter(**{pk_name: pk_value})

        assert q.count() == 1, "query result count != 1"

        q.update(**d) if d else None
        
        obj = q.first()
        
        self.after_post(request, obj)

        return JsonResponse({"message": "ok"})


class 抽象任务制作接口(APIView):
    def get(self, request, cls):
        print(request.GET)
        return JsonResponse(cls.得到一条任务json(request.GET.get("task_name")))

    def post(self, request, cls):
        rtn = {"messsage": "ok"}
        try:
            obj = cls.objects.get(id=request.POST.get("id"))
            obj.设置制作结果(request.POST["task_name"], request.POST["task_value"])
        except Exception as e:
            print(e)
            rtn["messsage"] = str(e)
        return JsonResponse(rtn)
