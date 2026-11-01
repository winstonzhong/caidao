# weixin_tools/tool_native_pay.py
"""
微信支付 Native（扫码）支付 —— API v2 纯函数封装

与项目无关的通用支付能力：统一下单、回调验签、主动查单。
所有商户配置（appid / mch_id / apiv2_key / notify_url）均由调用方以参数注入，
本模块不读任何配置文件、不内置任何密钥（密钥管理规范见 docs/native_pay_integration.md）。

依赖：requests、weixin_tools.helper_native_pay（签名/XML/订单号）

>>> nonce = generate_nonce_str()
>>> len(nonce) == 32 and all(c in '0123456789abcdef' for c in nonce)
True

>>> # verify_notify_xml：用假密钥构造一份带正确签名的回调 XML，验签通过
>>> from weixin_tools.helper_native_pay import generate_wechat_pay_sign, dict_to_xml
>>> _params = {'return_code': 'SUCCESS', 'result_code': 'SUCCESS',
...            'out_trade_no': 'ORDER_1700000000_1234', 'total_fee': '990'}
>>> _params['sign'] = generate_wechat_pay_sign(_params, 'fake_key_for_doctest_only')
>>> _xml = dict_to_xml(_params)
>>> result = verify_notify_xml(_xml, 'fake_key_for_doctest_only')
>>> result['out_trade_no']
'ORDER_1700000000_1234'

>>> # 密钥错误（签名不匹配）→ 抛 ValueError
>>> verify_notify_xml(_xml, 'wrong_key')
Traceback (most recent call last):
...
ValueError: 签名验证失败

>>> # 回调 return_code 非 SUCCESS → 抛 ValueError
>>> verify_notify_xml(dict_to_xml({'return_code': 'FAIL', 'return_msg': '系统错误'}), 'k')
Traceback (most recent call last):
...
ValueError: 回调数据异常: 系统错误

>>> # 非法 XML → 抛 ValueError
>>> verify_notify_xml('not xml at all', 'k')
Traceback (most recent call last):
...
ValueError: XML解析失败
"""
import random

import requests

from weixin_tools.helper_native_pay import (
    generate_wechat_pay_sign, dict_to_xml, xml_to_dict,
)

UNIFIED_ORDER_URL = "https://api.mch.weixin.qq.com/pay/unifiedorder"
ORDER_QUERY_URL = "https://api.mch.weixin.qq.com/pay/orderquery"


def generate_nonce_str(length=32):
    """生成随机 nonce_str（十六进制），每次下单/查单重新生成，不要使用固定值"""
    return "".join(random.choices("0123456789abcdef", k=length))


def _post_pay_api(url, params, apiv2_key, timeout):
    """签名 → 转 XML → POST → 解析响应，返回响应 dict"""
    params["sign"] = generate_wechat_pay_sign(params, apiv2_key)
    response = requests.post(
        url,
        data=dict_to_xml(params).encode("utf-8"),
        headers={"Content-Type": "text/xml"},
        timeout=timeout,
    )
    return xml_to_dict(response.content)


def create_native_order(*, appid, mch_id, apiv2_key, notify_url, body,
                        out_trade_no, total_fee, spbill_create_ip,
                        trade_type="NATIVE", timeout=10):
    """
    调用微信支付统一下单（v2），生成扫码支付二维码链接。

    :param total_fee: 金额，单位：分
    :return: {'out_trade_no': ..., 'code_url': ..., 'raw': 微信原始响应dict}
    :raises ValueError: 微信侧下单失败（return_code/result_code 非 SUCCESS 或无 code_url）
    """
    pay_params = {
        "appid": appid,
        "mch_id": mch_id,
        "nonce_str": generate_nonce_str(),
        "body": body,
        "out_trade_no": out_trade_no,
        "total_fee": total_fee,
        "spbill_create_ip": spbill_create_ip,
        "notify_url": notify_url,
        "trade_type": trade_type,
    }
    result = _post_pay_api(UNIFIED_ORDER_URL, pay_params, apiv2_key, timeout)

    if result.get("return_code") != "SUCCESS":
        raise ValueError(f"下单失败: {result.get('return_msg', '未知错误')}")
    if result.get("result_code") != "SUCCESS":
        raise ValueError(f"下单失败: {result.get('err_code_des') or result.get('err_msg') or '未知错误'}")

    code_url = result.get("code_url", "")
    if not code_url:
        raise ValueError("未获取到支付二维码链接")

    return {
        "out_trade_no": out_trade_no,
        "code_url": code_url,
        "raw": result,
    }


def verify_notify_xml(xml_data, apiv2_key):
    """
    解析并验签微信支付 v2 回调 XML。

    :return: 验签通过后的回调 dict（已弹出 sign 字段）
    :raises ValueError: XML 非法、return_code 非 SUCCESS、签名不匹配
    """
    result = xml_to_dict(xml_data)
    if not result or result.get("status") == "fail":
        raise ValueError("XML解析失败")
    if result.get("return_code") != "SUCCESS":
        raise ValueError(f"回调数据异常: {result.get('return_msg', '')}")

    sign = result.pop("sign", "")
    if generate_wechat_pay_sign(result, apiv2_key) != sign:
        raise ValueError("签名验证失败")

    return result


def query_native_order(*, appid, mch_id, apiv2_key, out_trade_no, timeout=10):
    """
    主动调用微信支付查单接口（v2 pay/orderquery）。
    用于 notify 回调丢失时的兜底对账；返回 dict 中 trade_state 为微信支付状态
    （SUCCESS / NOTPAY / CLOSED / REFUND ...）。

    :return: 微信原始响应 dict（return_code/result_code 均为 SUCCESS）
    :raises ValueError: 查询失败
    """
    params = {
        "appid": appid,
        "mch_id": mch_id,
        "nonce_str": generate_nonce_str(),
        "out_trade_no": out_trade_no,
    }
    result = _post_pay_api(ORDER_QUERY_URL, params, apiv2_key, timeout)

    if result.get("return_code") != "SUCCESS":
        raise ValueError(f"查单失败: {result.get('return_msg', '未知错误')}")
    if result.get("result_code") != "SUCCESS":
        raise ValueError(f"查单失败: {result.get('err_code_des') or result.get('err_msg') or '未知错误'}")

    return result


if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))
