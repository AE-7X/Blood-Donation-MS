from django.db import models
from django.db import models
import uuid
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from datetime import timedelta
from django.db import models
import uuid

class Donor(models.Model):
    # Basic Info
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    age = models.IntegerField(default=18)
    gender = models.CharField(max_length=10)
    state = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    blood_group = models.CharField(
        max_length=5,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('O+', 'O+'), ('O-', 'O-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
        ]
    )
    location = models.CharField(max_length=200)
    last_donated = models.DateField(null=True, blank=True)
    available = models.BooleanField(default=True)

    # 🩸 New field
    last_donation_date = models.DateField(null=True, blank=True)

    def is_eligible(self):
        """Check if donor is eligible to donate again (after 90 days)."""
        if not self.last_donation_date:
            return True
        next_eligible_date = self.last_donation_date + timedelta(days=90)
        return timezone.now().date() >= next_eligible_date

    def next_eligible_date(self):
        """Returns the next eligible donation date."""
        if not self.last_donation_date:
            return None
        return self.last_donation_date + timedelta(days=90)
    
    # Authentication & Verification
    password = models.CharField(max_length=128)  # Hashed password
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)

    # Profile Image
    profile_pic = models.ImageField(upload_to="profile_pics/", blank=True, null=True)

    # Donor Engagement / Badge System
    total_donations = models.PositiveIntegerField(default=0)
    BADGE_CHOICES = [
        ("New Donor", "New Donor"),
        ("Regular Donor", "Regular Donor"),
        ("Life Saver", "Life Saver"),
        ("Hero", "Hero"),
    ]
    badge = models.CharField(max_length=20, choices=BADGE_CHOICES, default="New Donor")

    def update_badge(self):
        """
        Automatically updates donor badge based on total_donations.
        Called whenever a new donation is recorded.
        """
        if self.total_donations >= 10:
            new_badge = "Hero"
        elif self.total_donations >= 5:
            new_badge = "Life Saver"
        elif self.total_donations >= 2:
            new_badge = "Regular Donor"
        else:
            new_badge = "New Donor"

        if self.badge != new_badge:
            self.badge = new_badge
            self.save(update_fields=["badge"])

    def __str__(self):
        return f"{self.name} ({self.blood_group})"

    

class DonorHealthCheck(models.Model):
    donor = models.ForeignKey(
        "Donor",
        on_delete=models.CASCADE,
        null=True,       
        blank=True
    )
    age = models.PositiveIntegerField()
    weight = models.FloatField(help_text="Weight in kg")
    hemoglobin_level = models.FloatField(help_text="g/dL")

    recent_illness = models.BooleanField(default=False, help_text="Any recent illness in the last 2 weeks?")
    medication = models.BooleanField(default=False, help_text="Currently taking any medications?")
    alcohol_24h = models.BooleanField(default=False, help_text="Consumed alcohol in the last 24 hours?")
    smoking = models.BooleanField(default=False, help_text="Smoked in the last 24 hours?")
    tattoo_6m = models.BooleanField(default=False, help_text="Had a tattoo/piercing in the last 6 months?")
    surgery_6m = models.BooleanField(default=False, help_text="Undergone surgery in the last 6 months?")
    chronic_disease = models.BooleanField(default=False, help_text="Any chronic diseases (Diabetes, Heart, Cancer, etc.)?")
    pregnant = models.BooleanField(default=False, help_text="Currently pregnant?")
    covid_recent = models.BooleanField(default=False, help_text="COVID-19 positive in the last 28 days?")
    travel_malaria = models.BooleanField(default=False, help_text="Traveled to malaria-prone areas in the last 3 months?")

    eligible = models.BooleanField(default=False)
    checked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.donor:
            return f"Health Check - {self.donor}"
        return "Health Check (Anonymous)"



class BloodRequest(models.Model):
    patient_name = models.CharField(max_length=100)
    hospital_name = models.CharField(max_length=100)
    blood_group_needed = models.CharField(max_length=10)
    location = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    age = models.PositiveIntegerField()  
    gender = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=50)     
    district = models.CharField(max_length=50) 
    status = models.CharField(max_length=20, default="pending")    
    urgent = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.patient_name} - {self.blood_group_needed}"

class Hospital(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    location = models.CharField(max_length=200)
    password = models.CharField(max_length=255)  

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.name
    


class Donation(models.Model):
    donor = models.ForeignKey('Donor', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.donor.name} - {self.date}"
    

class HospitalDonationRequest(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="donation_requests")
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    blood_group = models.CharField(max_length=5)
    units = models.PositiveIntegerField(default=1)
    requested_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.donor.name} → {self.hospital.name}"

class DonorRequest(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="donor_requests")
    donor_name = models.CharField(max_length=200)
    donor_age = models.IntegerField()
    donor_blood_group = models.CharField(max_length=5)
    donor_contact = models.CharField(max_length=15)
    status_choices = [
        ("Pending", "Pending"),
        ("Accepted", "Accepted"),
        ("Rejected", "Rejected"),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  
    def __str__(self):
        return f"{self.donor_name} - {self.hospital.name}"
    

# feedback model

class Feedback(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.name}"
    


# models.py
from django.db import models
from django.utils import timezone

class BloodStock(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='blood_stocks')
    blood_type = models.CharField(max_length=5)
    units = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField()

    def __str__(self):
        return f"{self.hospital.name} - {self.blood_type}"