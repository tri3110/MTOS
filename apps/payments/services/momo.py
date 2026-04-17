import json
import uuid
import requests
import hmac
import hashlib

class MomoService:

    endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"

    accessKey = "F8BBA842ECF85"
    secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
    partnerCode = "MOMO"

    @classmethod
    def create_payment(cls, order):

        orderId = str(uuid.uuid4())
        requestId = str(uuid.uuid4())
        amount = str(int(order.total_price))
        orderInfo = f"Thanh toán đơn {order.id}"
        redirectUrl = f"http://localhost:3000/payment?orderId={order.id}"
        ipnUrl = "http://localhost:8000//api/user/momo-ipn/"

        extraData = ""
        requestType = "payWithMethod"

        rawSignature = (
            f"accessKey={cls.accessKey}"
            f"&amount={amount}"
            f"&extraData={extraData}"
            f"&ipnUrl={ipnUrl}"
            f"&orderId={orderId}"
            f"&orderInfo={orderInfo}"
            f"&partnerCode={cls.partnerCode}"
            f"&redirectUrl={redirectUrl}"
            f"&requestId={requestId}"
            f"&requestType={requestType}"
        )

        signature = hmac.new(
            cls.secretKey.encode(),
            rawSignature.encode(),
            hashlib.sha256
        ).hexdigest()

        data = {
            "partnerCode": cls.partnerCode,
            "orderId": orderId,
            "ipnUrl": ipnUrl,
            "amount": amount,
            "requestType": requestType,
            "paymentCode": "ATM",
            "redirectUrl": redirectUrl,
            "orderInfo": orderInfo,
            "requestId": requestId,
            "extraData": extraData,
            "signature": signature,
            "lang": "vi"
        }

        response = requests.post(cls.endpoint, json=data)
        return response.json()