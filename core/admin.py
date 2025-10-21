from django.contrib import admin
from .models import Donor, Donation

@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'blood_group', 'total_donations', 'badge')
    search_fields = ('name', 'email', 'phone')

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor', 'date', 'location')
    search_fields = ('donor__name',)


from .models import Feedback

admin.site.register(Feedback)