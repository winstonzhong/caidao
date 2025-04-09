from rest_framework.views import APIView
from django.http.response import JsonResponse

# Create your views here.

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
