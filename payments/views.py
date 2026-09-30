from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Payment
from .mpesa import stk_push

@api_view(["POST"])
def start_payment(request):
    phone = str(request.data.get("phone", "")).strip()
    amount = int(request.data.get("amount", 0))
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    if not (phone.startswith("254") and len(phone) == 12 and amount > 0):
        return Response({"error": "Invalid phone or amount"}, status=400)

    payment = Payment.objects.create(phone=phone, amount=amount)
    data = stk_push(phone, amount)
    if data.get("ResponseCode") == "0":
        payment.checkout_request_id = data["CheckoutRequestID"]
        payment.save()
        return Response({"payment_id": payment.id, "message": "Check your phone"})
    payment.status = Payment.Status.FAILED
    payment.result_desc = data.get("errorMessage", "Request failed")
    payment.save()
    return Response({"error": payment.result_desc}, status=502)

@api_view(["POST"])
def callback(request):
    cb = request.data.get("Body", {}).get("stkCallback", {})
    payment = Payment.objects.filter(checkout_request_id=cb.get("CheckoutRequestID")).first()
    if payment:
        payment.result_desc = cb.get("ResultDesc", "")
        if cb.get("ResultCode") == 0:
            items = {i["Name"]: i.get("Value") for i in cb["CallbackMetadata"]["Item"]}
            payment.status = Payment.Status.SUCCESS
            payment.mpesa_receipt = items.get("MpesaReceiptNumber", "")
        else:
            payment.status = Payment.Status.FAILED
        payment.save()
    return Response({"ResultCode": 0, "ResultDesc": "Accepted"})

@api_view(["GET"])
def payment_status(request, pk):
    p = Payment.objects.get(pk=pk)
    return Response({"status": p.status, "receipt": p.mpesa_receipt, "message": p.result_desc})