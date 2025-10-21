from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Donor
    path('register/', views.donor_register, name='donor_register'),
    path('login/donor/', views.donor_login, name='donor_login'),
    path('logout/donor/', views.donor_logout, name='donor_logout'),
    path('donor/delete/<int:donor_id>/', views.delete_donor, name='delete_donor'),
    path('profile/donor/', views.donor_profile, name='donor_profile'),
    path('profile/donor/edit/', views.edit_donor_profile, name='edit_donor_profile'),

    # Donor email verification
    path('verify/<uuid:token>/', views.verify_donor_email, name='verify_donor_email'),

    # Search & Requests
    path('search/', views.search_donors, name='search_donors'),
    path('request/', views.request_blood, name='request_blood'),
    path('blood-requests/', views.blood_requests_list, name='blood_requests_list'),

    # Hospital
    path('hospital/register/', views.hospital_register, name='hospital_register'),
    path('hospital/dashboard/', views.hospital_dashboard, name='hospital_dashboard'),
    path('hospital/profile/', views.hospital_profile, name='hospital_profile'),
    path('hospital/edit/', views.edit_hospital_profile, name='edit_hospital_profile'),
    path('hospitals/', views.hospital_list, name='hospital_list'),
    path('login/hospital/', views.hospital_login, name='hospital_login'),
    path('logout/hospital/', views.hospital_logout, name='hospital_logout'),
    path('hospital/blood-request/add/', views.add_blood_request, name='add_blood_request'),

    # Public hospital profile + donor requests
    path('hospital/<int:hospital_id>/', views.hospital_public_profile, name='hospital_public_profile'),
    path('accept_request/<int:req_id>/', views.accept_request, name='accept_request'),
    path('reject_request/<int:req_id>/', views.reject_request, name='reject_request'),
    
    # Donor requests visible to hospital authority
    path("hospital/<int:hospital_id>/donate/", views.donor_request_view, name="donor_request"),

    # Health Check
    path("health-check/", views.detailed_health_check, name="detailed_health_check"),
    
    # Feedback
    path('feedback/', views.feedback_view, name='feedback'),

    # Live Blood Stock
    path('live-stock/', views.live_stock, name='live_stock'),
    path('hospital/manage_blood_stock/', views.manage_blood_stock, name='manage_blood_stock'),
    path('hospital/delete_stock/<int:stock_id>/', views.delete_blood_stock, name='delete_blood_stock'),


]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
