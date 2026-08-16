/**
 * wx_native_pay.js —— 微信 Native 扫码支付前端组件（caidao 公用）
 *
 * 自包含支付弹窗：创建订单 → 渲染支付二维码 → 轮询支付结果 → 成功回调。
 * 外部依赖：jQuery、QRCode.js（qrcodejs，页面需先引入 qrcode.min.js）。
 *
 * 用法：
 *   WxNativePay.open({
 *     createUrl: '/daiban/wechat/pay/create',   // 创建订单接口（POST form: goods_name）
 *     queryUrl:  '/daiban/wechat/pay/query',    // 订单状态查询接口（GET: out_trade_no）
 *     goodsName: '基础套餐',
 *     amountText: '支付金额：¥99',               // 金额展示文案
 *     onPaid: function (orderData) { ... },     // 支付成功回调（业务方接：开通权益等）
 *     onError: function (msg) { ... }           // 可选，默认 alert
 *   });
 *   WxNativePay.close();                        // 主动关闭（停止轮询）
 *
 * 后端接口约定（与 weixin_tools/django_native_pay.py 的 view 工厂一致）：
 *   createUrl 响应：{code:200, data:{out_trade_no, code_url, amount}}
 *   queryUrl  响应：{code:200, data:{out_trade_no, status}}，status === '已支付' 视为支付成功
 */
(function (window, $) {
    'use strict';

    var MODAL_ID = 'wxNativePayModal';
    var QR_ID = 'wxNativePayQrcode';

    var state = {
        timer: null,
        outTradeNo: null,
        options: null
    };

    function ensureModal() {
        if (document.getElementById(MODAL_ID)) return;

        var css =
            '#' + MODAL_ID + '{position:fixed;inset:0;background:rgba(0,0,0,.6);display:flex;' +
            'align-items:center;justify-content:center;z-index:9999;padding:12px;}' +
            '#' + MODAL_ID + ' .wxnp-box{background:#16213e;border-radius:16px;padding:24px;' +
            'width:100%;max-width:400px;box-shadow:0 20px 60px rgba(0,0,0,.5);color:#fff;' +
            'font-family:inherit;}' +
            '#' + MODAL_ID + ' .wxnp-head{display:flex;justify-content:space-between;' +
            'align-items:center;margin-bottom:20px;}' +
            '#' + MODAL_ID + ' .wxnp-title{font-size:18px;font-weight:500;}' +
            '#' + MODAL_ID + ' .wxnp-close{background:none;border:none;color:#9ca3af;' +
            'font-size:22px;cursor:pointer;line-height:1;padding:0;}' +
            '#' + MODAL_ID + ' .wxnp-close:hover{color:#fff;}' +
            '#' + MODAL_ID + ' .wxnp-amount{text-align:center;font-size:16px;margin-bottom:16px;}' +
            '#' + MODAL_ID + ' .wxnp-qr-wrap{width:192px;height:192px;background:#fff;margin:0 auto 16px;' +
            'border-radius:8px;display:flex;align-items:center;justify-content:center;}' +
            '#' + MODAL_ID + ' .wxnp-tip{text-align:center;color:#d1d5db;font-size:13px;}' +
            '#' + MODAL_ID + ' .wxnp-tip-sub{text-align:center;color:#9ca3af;font-size:12px;margin-top:8px;}' +
            '#' + MODAL_ID + ' .wxnp-actions{display:flex;justify-content:center;margin-top:20px;}' +
            '#' + MODAL_ID + ' .wxnp-cancel{padding:8px 24px;background:rgba(255,255,255,.1);' +
            'border:none;border-radius:8px;color:#fff;cursor:pointer;font-size:14px;}' +
            '#' + MODAL_ID + ' .wxnp-cancel:hover{background:rgba(255,255,255,.2);}';

        var style = document.createElement('style');
        style.textContent = css;
        document.head.appendChild(style);

        var html =
            '<div id="' + MODAL_ID + '" style="display:none;">' +
            '  <div class="wxnp-box">' +
            '    <div class="wxnp-head">' +
            '      <div class="wxnp-title">微信扫码支付</div>' +
            '      <button class="wxnp-close" type="button">&times;</button>' +
            '    </div>' +
            '    <div class="wxnp-amount"></div>' +
            '    <div class="wxnp-qr-wrap"><div id="' + QR_ID + '" style="width:160px;height:160px;"></div></div>' +
            '    <p class="wxnp-tip">请使用微信扫描二维码完成支付</p>' +
            '    <p class="wxnp-tip-sub">支付完成后自动验证，请勿刷新页面</p>' +
            '    <div class="wxnp-actions"><button class="wxnp-cancel" type="button">取消支付</button></div>' +
            '  </div>' +
            '</div>';

        $('body').append(html);
        $('#' + MODAL_ID).find('.wxnp-close, .wxnp-cancel').on('click', function () {
            WxNativePay.close();
        });
    }

    function defaultError(msg) {
        alert(msg);
    }

    function handleError(msg) {
        var fn = (state.options && state.options.onError) || defaultError;
        fn(msg);
    }

    function stopPolling() {
        if (state.timer) {
            clearInterval(state.timer);
            state.timer = null;
        }
    }

    function startPolling() {
        stopPolling();
        var opts = state.options;
        state.timer = setInterval(function () {
            $.ajax({
                url: opts.queryUrl,
                type: 'GET',
                data: { out_trade_no: state.outTradeNo },
                dataType: 'json',
                success: function (res) {
                    if (res.code === 200 && res.data) {
                        if (res.data.status === '已支付') {
                            var orderData = {
                                out_trade_no: state.outTradeNo,
                                goods_name: opts.goodsName
                            };
                            WxNativePay.close();
                            if (typeof opts.onPaid === 'function') {
                                opts.onPaid(orderData);
                            }
                        }
                    } else {
                        console.log('查询订单状态失败：', res.msg);
                    }
                },
                error: function (xhr, status, error) {
                    console.log('轮询订单状态请求失败：', error);
                }
            });
        }, opts.pollInterval || 3000);
    }

    function renderQrcode(codeUrl) {
        if (!codeUrl) return;
        var el = document.getElementById(QR_ID);
        el.innerHTML = '';
        new QRCode(el, {
            text: codeUrl,
            colorDark: '#000000',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.H
        });
    }

    function createOrder() {
        var opts = state.options;
        $.ajax({
            url: opts.createUrl,
            type: 'POST',
            data: { goods_name: opts.goodsName },
            dataType: 'json',
            success: function (res) {
                if (res.code === 200 && res.data) {
                    state.outTradeNo = res.data.out_trade_no;
                    renderQrcode(res.data.code_url);
                    startPolling();
                } else {
                    handleError('生成支付二维码失败：' + (res.msg || '未知错误'));
                }
            },
            error: function () {
                handleError('请求后端失败，请检查接口是否可用或网络状态');
            }
        });
    }

    window.WxNativePay = {
        /**
         * 打开支付弹窗并开始支付流程
         * @param {Object} options 见文件头注释
         */
        open: function (options) {
            ensureModal();
            this.close();
            state.options = options || {};
            $('#' + MODAL_ID).find('.wxnp-amount').text(state.options.amountText || '');
            $('#' + MODAL_ID).show();
            createOrder();
        },

        /** 关闭支付弹窗（停止轮询、清空二维码） */
        close: function () {
            stopPolling();
            state.outTradeNo = null;
            var modal = document.getElementById(MODAL_ID);
            if (modal) {
                modal.style.display = 'none';
                var qr = document.getElementById(QR_ID);
                if (qr) qr.innerHTML = '';
            }
        }
    };
})(window, jQuery);
