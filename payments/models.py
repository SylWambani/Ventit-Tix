from django.db import models

class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        SUCCESS = "success"
        FAILED = "failed"

    phone = models.CharField(max_length=12)
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    checkout_request_id = models.CharField(max_length=100, blank=True, db_index=True)
    mpesa_receipt = models.CharField(max_length=30, blank=True)
    result_desc = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)