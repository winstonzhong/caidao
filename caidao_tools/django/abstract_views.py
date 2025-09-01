import json
from rest_framework.views import APIView
from django.http.response import JsonResponse, HttpResponse
from django.utils import timezone

# Create your views here.
import tool_env


class 基础任务视图(APIView):
    @property
    def model(self):
        raise NotImplementedError

    def before_get(self, request):
        d = self.model.筛选出数据库字段(request.GET)
        for k, v in d.items():
            if v in ("False", "True"):
                d[k] = eval(v)
            elif v == "None":
                d[k] = None
        return d

    def get_order_by(self, request):
        if request.GET.get("order_by"):
            return [
                x for x in request.GET.get("order_by").strip().split(",") if x.strip()
            ]

        if request.GET.get("wait_finished") is not None:
            return ["id"]
        return ["update_time"]

    def get(self, request):
        d = self.before_get(request)
        obj = (
            self.model.objects.filter(**d).order_by(*self.get_order_by(request)).first()
        )

        if request.GET.get("wait_finished") is not None:
            obj = self.model.尝试获得处理权(obj)
        elif obj is not None:
            obj.save()

        obj = self.after_get(request, obj)

        if isinstance(obj, str):
            return HttpResponse(obj)
        elif isinstance(obj, list) or isinstance(obj, dict):
            return JsonResponse(obj)
        elif obj is not None:
            return JsonResponse(obj.json)
        else:
            return JsonResponse({})

    def after_get(self, request, obj):
        return obj

    def after_post(self, request, obj):
        pass

    def post(self, request):
        d = request.POST.dict()

        pk_name = d.get("pk_name", "pk")

        pk_value = d.get("pk_value")

        # assert pk_name and pk_value, "pk_name or pk_value is None"
        # print('pk_name', pk_name, 'pk_value', pk_value)

        if pk_name and pk_value:
            d = self.model.筛选出数据库字段(d)

            q = self.model.objects.filter(**{pk_name: pk_value})

            assert q.count() == 1, "query result count != 1"

            # assert tool_env.is_int(d.get("due_time", 0)), "due_time is not int"

            obj = q.first()

            if d:
                for k, v in d.items():
                    setattr(obj, k, v)
                obj.save()
        else:
            obj = None
            # print("pk_name or pk_value is None")

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
