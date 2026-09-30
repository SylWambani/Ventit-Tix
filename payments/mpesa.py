import base64, os, requests
from datetime import datetime

BASE = "https://sandbox.safaricom.co.ke"

def get_token():
    r = requests.get(
        f"{BASE}/oauth/v1/generate?grant_type=client_credentials",
        auth=(os.getenv("MPESA_CONSUMER_KEY"), os.getenv("MPESA_CONSUMER_SECRET")),
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["access_token"]

def stk_push(phone, amount, reference="Venit Tickets"):
    shortcode = os.getenv("MPESA_SHORTCODE")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        f"{shortcode}{os.getenv('MPESA_PASSKEY')}{timestamp}".encode()
    ).decode()

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,          
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": os.getenv("MPESA_CALLBACK_URL"),
        "AccountReference": reference,
        "TransactionDesc": "Ticket payment",
    }
    r = requests.post(
        f"{BASE}/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers={"Authorization": f"Bearer {get_token()}"},
        timeout=15,
    )
    return r.json()