from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Payment
from .mpesa import stk_push

TICKET_TYPES = {
    "regular": {"name": "Regular", "price": 500},
    "vip": {"name": "VIP", "price": 1500},
}

@api_view(["GET"])
def ticket_types(request):
    return Response(TICKET_TYPES)


@api_view(["POST"])
def start_payment(request):
    phone = str(request.data.get("phone", "")).strip()
    ticket_id = request.data.get("ticket_id")
    quantity = request.data.get("quantity", 1)

    ticket = TICKET_TYPES.get(ticket_id)
    if not ticket:
        return Response({"error": "Invalid ticket type"}, status=400)

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return Response({"error": "Invalid quantity"}, status=400)
    if quantity < 1 or quantity > 10:
        return Response({"error": "Quantity must be between 1 and 10"}, status=400)

    amount = ticket["price"] * quantity  

    if phone.startswith("0"):
        phone = "254" + phone[1:]
    if not (phone.startswith("254") and len(phone) == 12):
        return Response({"error": "Invalid phone number"}, status=400)

    payment = Payment.objects.create(phone=phone, amount=amount)
    data = stk_push(phone, amount)
    if data.get("ResponseCode") == "0":
        payment.checkout_request_id = data["CheckoutRequestID"]
        payment.save()
        return Response({"payment_id": payment.id, "amount": amount, "message": "Check your phone"})
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