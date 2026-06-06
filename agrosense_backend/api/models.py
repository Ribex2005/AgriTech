from django.db import models


class Disease(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    crop = models.CharField(max_length=200, null=True, blank=True)  # NEW
    symptoms = models.TextField(null=True, blank=True)
    treatment = models.TextField(null=True, blank=True)
    prevention = models.TextField(null=True, blank=True)
    severity = models.CharField(max_length=50, null=True, blank=True)
    reference = models.URLField(null=True, blank=True)  # NEW

    def __str__(self):
        return self.name or "Disease"


class MarketPrice(models.Model):
    crop_name = models.CharField(max_length=200, null=True, blank=True)
    market_location = models.CharField(max_length=200, null=True, blank=True)
    price_per_unit = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.crop_name} - {self.market_location}"


class Scheme(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    benefits = models.TextField(null=True, blank=True)
    eligibility = models.TextField(null=True, blank=True)
    application_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name or "Scheme"


# ✅ OPTIONAL (VERY USEFUL FOR FUTURE)
class DiseasePrediction(models.Model):
    crop_name = models.CharField(max_length=200)
    disease_name = models.CharField(max_length=200)
    confidence = models.FloatField()  # NEW (important)
    image_path = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.crop_name} - {self.disease_name} ({self.confidence}%)"