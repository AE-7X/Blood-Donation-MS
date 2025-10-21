from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

from .models import BloodRequest, Donor

@receiver(post_save, sender=BloodRequest)
def send_urgent_blood_request_email(sender, instance, created, **kwargs):
    if created and instance.urgent:
        # Fetch all verified donors
        donors = Donor.objects.filter(is_verified=True)
        recipient_list = [donor.email for donor in donors if donor.email]

        if recipient_list:
            subject = f"URGENT Blood Request: {instance.blood_group_needed}"
            html_content = render_to_string(
                'urgent_blood_request.html',  # Your new template path
                {
                    'patient_name': instance.patient_name,
                    'hospital_name': instance.hospital_name,
                    'blood_group_needed': instance.blood_group_needed,
                    'location': instance.location,
                    'contact_number': instance.contact_number,
                    'age': instance.age,
                    'gender': instance.gender,
                }
            )

            email = EmailMessage(
                subject,
                html_content,
                settings.EMAIL_HOST_USER,
                recipient_list,
            )
            email.content_subtype = 'html'  # Send as HTML
            email.send(fail_silently=False)
