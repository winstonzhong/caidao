# weixin_tools/django_native_pay.py
"""
微信支付 Native（扫码）支付 —— 通用 Django view 工厂

在 tool_native_pay（纯函数）之上提供可直接挂载到 urls.py 的 Django 视图。
各项目的业务逻辑（定价、订单落库、支付成功后的开通动作、登录校验）全部通过
钩子函数 / 装饰器注入，本模块不依赖任何具体项目的 model。

用法示例见 docs/native_pay_integration.md。
"""
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from weixin_tools.helper_native_pay import dict_to_xml, generate_order_no
from weixin_tools.tool_native_pay import create_native_order, verify_notify_xml


def _apply_decorators(view_func, decorators):
    for decorator in decorators:
        view_func = decorator(view_func)
    return view_func


def make_create_order_view(*, appid, mch_id, apiv2_key, notify_url,
                           resolve_amount, on_order_created,
                           trade_type="NATIVE", decorators=()):
    """
    生成「创建 Native 支付订单」视图（POST form: goods_name）。

    :param resolve_amount: fn(goods_name, request) -> float，返回商品真实金额（元）。
                           金额必须由后端定价决定，禁止信任前端传来的金额。
                           商品非法时抛 ValueError（以其消息作为 400 响应 msg）。
    :param on_order_created: fn(request, *, out_trade_no, goods_name, amount, code_url, raw)
                             下单成功后的订单落库钩子。amount 单位：元。
    :param decorators: 需要追加的装饰器（如 csrf_exempt、登录校验装饰器）。
    """
    def view(request):
        if request.method != "POST":
            return JsonResponse({"code": 400, "msg": "仅支持POST请求"})

        goods_name = request.POST.get("goods_name", "")
        try:
            amount = float(resolve_amount(goods_name, request))
        except ValueError as e:
            return JsonResponse({"code": 400, "msg": str(e)})
        if amount <= 0:
            return JsonResponse({"code": 400, "msg": "支付金额必须大于0"})

        out_trade_no = generate_order_no()
        total_fee = int(amount * 100)  # 转换为分
        try:
            order = create_native_order(
                appid=appid, mch_id=mch_id, apiv2_key=apiv2_key,
                notify_url=notify_url, body=goods_name,
                out_trade_no=out_trade_no, total_fee=total_fee,
                spbill_create_ip=request.META.get("REMOTE_ADDR", "127.0.0.1"),
                trade_type=trade_type,
            )
        except ValueError as e:
            return JsonResponse({"code": 500, "msg": str(e)})

        on_order_created(request, out_trade_no=out_trade_no, goods_name=goods_name,
                         amount=amount, code_url=order["code_url"], raw=order["raw"])

        return JsonResponse({
            "code": 200,
            "msg": "支付二维码生成成功",
            "data": {
                "out_trade_no": out_trade_no,
                "code_url": order["code_url"],
                "amount": amount,
            }
        })

    return _apply_decorators(view, decorators)


def make_notify_view(*, apiv2_key, on_paid):
    """
    生成「微信支付结果回调」视图（微信服务器 POST XML，已挂 csrf_exempt）。

    :param on_paid: fn(notify_dict)，支付成功（result_code == SUCCESS）时调用，
                    参数为验签通过后的回调 dict（含 out_trade_no/openid/total_fee 等）。
                    抛出的异常会向上传播，微信将按规则重推回调。
    """
    @csrf_exempt
    def view(request):
        if request.method != "POST":
            return HttpResponse(dict_to_xml({"return_code": "FAIL", "return_msg": "仅支持POST请求"}))

        try:
            result = verify_notify_xml(request.body, apiv2_key)
        except ValueError as e:
            return HttpResponse(dict_to_xml({"return_code": "FAIL", "return_msg": str(e)}))

        if result.get("result_code") == "SUCCESS":
            on_paid(result)

        return HttpResponse(dict_to_xml({"return_code": "SUCCESS", "return_msg": "OK"}))

    return view


def make_query_status_view(*, get_status, decorators=()):
    """
    生成「订单状态查询」视图（GET: out_trade_no），供前端轮询。

    :param get_status: fn(out_trade_no) -> str，查询业务订单表返回状态
                       （如 "待支付" / "已支付"），订单不存在时返回 None。
    :param decorators: 需要追加的装饰器（如登录校验装饰器）。
    """
    def view(request):
        out_trade_no = request.GET.get("out_trade_no", "")
        if not out_trade_no:
            return JsonResponse({"code": 400, "msg": "缺少订单号"})

        order_status = get_status(out_trade_no) or "待支付"
        return JsonResponse({
            "code": 200,
            "msg": "订单状态查询成功",
            "data": {
                "out_trade_no": out_trade_no,
                "status": order_status,
            }
        })

    return _apply_decorators(view, decorators)
