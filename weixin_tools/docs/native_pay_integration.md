# 微信 Native 扫码支付公用组件 — 接入指南

适用于「非微信生态浏览器（PC/手机网页）内的微信扫码支付」场景，基于微信支付 **API v2**
（XML 报文 + MD5 签名）。其他 Django 项目按本文档接入即可，无需复制任何实现代码。

## 组件构成

| 文件 | 说明 |
|---|---|
| `weixin_tools/tool_native_pay.py` | 纯函数层：`create_native_order`（统一下单）、`verify_notify_xml`（回调验签）、`query_native_order`（主动查单）。无 Django 依赖，可直接单测 |
| `weixin_tools/django_native_pay.py` | Django view 工厂：`make_create_order_view` / `make_notify_view` / `make_query_status_view`，业务逻辑全部钩子注入 |
| `weixin_tools/static/wx_native_pay.js` | 前端支付弹窗组件（依赖 jQuery + QRCode.js）：创建订单 → 二维码 → 轮询 → 成功回调 |
| `weixin_tools/helper_native_pay.py` | 已有底层工具：v2 MD5 签名、XML 互转、订单号生成、JWT（本组件复用，勿改） |

导入方式（caidao 目录本身已在各项目 `sys.path` 中）：

```python
from weixin_tools.tool_native_pay import create_native_order, verify_notify_xml, query_native_order
from weixin_tools.django_native_pay import make_create_order_view, make_notify_view, make_query_status_view
```

## 接入步骤

### 1. 配置（项目自己的 config.yml）

在项目自己的 `config/config.yml` 中准备以下配置项（值见微信支付商户平台）：

```yaml
APP_ID: "公众号/开放平台 appid"
MCH_ID: "商户号"
APIV2_KEY: "APIv2 密钥（商户平台-API安全）"
NATIVE_PAY_NOTIFY_URL: "https://你的域名/xxx/wechat/pay/notify"
NATIVE_TRADE_TYPE: "NATIVE"
```

settings.py 中读取（示例）：

```python
APP_ID = CONFIGS.get("APP_ID", "")
MCH_ID = CONFIGS.get("MCH_ID", "")
APIV2_KEY = CONFIGS.get("APIV2_KEY", "")
NATIVE_PAY_NOTIFY_URL = CONFIGS.get("NATIVE_PAY_NOTIFY_URL", "")
NATIVE_TRADE_TYPE = CONFIGS.get("NATIVE_TRADE_TYPE", "NATIVE")
```

### 2. 挂载视图（urls.py / views.py）

以 crawler 项目 daiban app 为完整示例：

```python
# views.py
from django.views.decorators.csrf import csrf_exempt
from weixin_tools.django_native_pay import (
    make_create_order_view, make_notify_view, make_query_status_view,
)
from my_project.settings import APP_ID, MCH_ID, APIV2_KEY, NATIVE_PAY_NOTIFY_URL, NATIVE_TRADE_TYPE
from .models import 都包订单, 订单状态_已支付, 套餐数据

def 解析套餐金额(goods_name, request):
    """定价钩子：金额必须由后端决定，禁止信任前端传来的金额"""
    info = 套餐数据.get(goods_name)
    if not info:
        raise ValueError("无效的套餐类型")   # 消息原样返回给前端（code:400）
    return float(info['amount'])

def 保存订单(request, *, out_trade_no, goods_name, amount, code_url, raw):
    """落库钩子：下单成功后保存业务订单"""
    unionid = request.user_info.get('unionid')   # request.user_info 由登录装饰器注入
    都包订单.创建订单(unionid, goods_name, out_trade_no, round(amount, 2), code_url, 数据=raw)

def 支付成功处理(result):
    """支付成功钩子：更新订单状态、开通权益等"""
    都包订单.更新支付状态(result.get('openid'), result.get('out_trade_no'),
                        result.get('total_fee'), 订单状态_已支付, 数据=result)

def 查询订单状态(out_trade_no):
    obj = 都包订单.objects.filter(订单号=out_trade_no).first()
    return obj.状态 if obj else None

create_native_order = make_create_order_view(
    appid=APP_ID, mch_id=MCH_ID, apiv2_key=APIV2_KEY,
    notify_url=NATIVE_PAY_NOTIFY_URL, trade_type=NATIVE_TRADE_TYPE,
    resolve_amount=解析套餐金额, on_order_created=保存订单,
    decorators=(csrf_exempt, check_login_middleware),   # 按需挂登录校验
)
wechat_pay_notify = make_notify_view(apiv2_key=APIV2_KEY, on_paid=支付成功处理)
query_order_status = make_query_status_view(
    get_status=查询订单状态, decorators=(csrf_exempt, check_login_middleware),
)
```

```python
# urls.py
urlpatterns = [
    path("wechat/pay/create", views.create_native_order),
    path("wechat/pay/notify", views.wechat_pay_notify),   # 与商户平台/代码中的 notify_url 一致
    path("wechat/pay/query", views.query_order_status),
]
```

接口约定（前端组件依赖此格式，勿改）：

- create：`POST form: goods_name` → `{code:200, data:{out_trade_no, code_url, amount}}`
- query：`GET ?out_trade_no=...` → `{code:200, data:{out_trade_no, status}}`，`status == "已支付"` 视为成功
- notify：微信 POST XML，验签通过后调用 `on_paid`，应答 XML `SUCCESS`

### 3. 前端接入

```html
<script src="qrcode.min.js"></script>           <!-- QRCode.js（qrcodejs） -->
<script src="jquery-3.7.1.min.js"></script>
<script src="/static/wx_native_pay.js"></script>
```

`wx_native_pay.js` 的静态分发：把 `caidao/weixin_tools/static` 加入 settings 的
`STATICFILES_DIRS`（与 sys.path 使用同一 caidao 路径），或发布到 CDN 后引用。

```js
WxNativePay.open({
    createUrl: HOST + '/xxx/wechat/pay/create',
    queryUrl:  HOST + '/xxx/wechat/pay/query',
    goodsName: '基础套餐',
    amountText: '支付金额：¥99',
    onPaid: function (orderData) {
        // 支付成功：刷新用户权益、弹成功提示等（业务逻辑）
    },
    onError: function (msg) { alert(msg); }     // 可选，默认 alert
});
```

## 敏感信息（密钥）管理规范 ⚠️

1. **密钥只存放在各使用项目自己的 `config/config.yml`**，由项目 settings.py 读取后以
   **函数参数**注入组件；caidao 组件本身不读任何配置文件、不内置任何密钥。
2. **caidao 仓库零密钥**：组件代码、doctest、本文档一律使用占位符；真实
   `MCH_ID` / `APIV2_KEY` / `APIV3_KEY` / `APP_SECRET` / `JWT_SECRET_KEY` 等
   **严禁写入 caidao 仓库的任何文件**，也严禁提交进版本库、推送远端。
3. 各项目的 `config/` 目录必须在项目 `.gitignore` 中（参考 crawler：`.gitignore` 忽略
   整个 `config/`，版本库只保留 `config.yml.default` 模板，模板中密钥值留空）。
4. `nonce_str` 由组件每次随机生成，不要在配置里使用固定值。
5. 签入前自查：`git status` 确认暂存区无 `config.yml`；`git check-ignore config/config.yml`
   确认命中忽略规则。

## 备注

- 当前仅覆盖 Native 扫码支付（v2）。公众号内 JSAPI 支付、退款、关单、v3 签名/验签
  不在本组件范围内，后续可按同模式追加。
- `query_native_order`（微信侧主动查单）可用于 notify 丢失时的兜底对账，默认链路
  （本地订单表 + notify 回调）不接它也能正常工作。
