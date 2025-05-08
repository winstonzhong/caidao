from rest_framework.views import APIView
from django.http.response import JsonResponse

# Create your views here.


class 基础任务视图(APIView):
    @property
    def model(self):
        raise NotImplementedError
    
    def get(self, request):
        d = self.model.筛选出数据库字段(request.GET)
        obj = self.model.objects.filter(**d).first()

        if obj is not None:
            return JsonResponse(obj.json)
        else:
            return JsonResponse({})




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
