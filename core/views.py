# ==============================
# Imports
# ==============================
import hashlib
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import timedelta
from django.utils import timezone
from .models import BloodStock


from .models import (
    Donor, BloodRequest, Hospital, Donation, DonorRequest, DonorHealthCheck, Feedback
)
from .forms import (
    HospitalDonationRequestForm, DonorRequestForm, DetailedHealthCheckForm, FeedbackForm
)
from .utils import HOSPITAL_NAMES


# ==============================
# Home / Public Views
# ==============================
def home(request):
    donor_registered = 'donor_email' in request.session
    hospital_registered = 'hospital_id' in request.session
    urgent_requests = BloodRequest.objects.filter(status='pending', urgent=True).order_by('-created_at')

    # --- New counts ---
    total_donors = Donor.objects.count()
    total_hospitals = Hospital.objects.count()
    total_requests = BloodRequest.objects.count()
    # -------------------

    # Feedback form handling
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you for your feedback!")
            return redirect('home')
    else:
        form = FeedbackForm()

    return render(request, 'home.html', {
        'donor_registered': donor_registered,
        'hospital_registered': hospital_registered,
        'urgent_requests': urgent_requests,
        'urgent_requests_count': urgent_requests.count(),
        'form': form,
        'total_donors': total_donors,
        'total_hospitals': total_hospitals,
        'total_requests': total_requests,
    })


def search_donors(request):
    donors = None
    if any(param in request.GET for param in ["blood_group", "state", "district"]):
        blood_group = request.GET.get("blood_group", "").strip()
        state = request.GET.get("state", "").strip()
        district = request.GET.get("district", "").strip()
        if blood_group or state or district:
            donors = Donor.objects.all()
            if blood_group: donors = donors.filter(blood_group__iexact=blood_group)
            if state: donors = donors.filter(state__icontains=state)
            if district: donors = donors.filter(district__icontains=district)
            if donors.exists():
                messages.success(request, f"✅ Found {donors.count()} donor(s).")
            else:
                messages.warning(request, "⚠️ No donors available for your search.")
                donors = None
        else:
            messages.warning(request, "⚠️ Please enter search criteria.")
    return render(request, "search_donors.html", {"donors": donors})


def hospital_public_profile(request, hospital_id):
    hospital = get_object_or_404(Hospital, id=hospital_id)
    
    # Get only stocks for this hospital
    stocks = hospital.blood_stocks.all().order_by('blood_group')

    if request.method == 'POST':
        form = HospitalDonationRequestForm(request.POST)
        if form.is_valid():
            donation_request = form.save(commit=False)
            donation_request.hospital = hospital
            if request.user.is_authenticated and hasattr(request.user, "donor"):
                donation_request.donor = request.user.donor
            donation_request.save()
            messages.success(request, "Donation request submitted successfully!")
            return redirect('hospital_public_profile', hospital_id=hospital.id)
    else:
        form = HospitalDonationRequestForm()
    
    return render(request, 'hospital_public_profile.html', {
        'hospital': hospital,
        'form': form,
        'stocks': stocks
    })


# ==============================
# Donor Registration & Login
# ==============================
def donor_register(request):
    if request.method == "POST":
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        age = request.POST.get("age")  
        gender = request.POST.get("gender")
        blood_group = request.POST['blood_group']
        state = request.POST.get('state', '')
        district = request.POST.get('district', '')
        location = request.POST.get('location', '')
        password = request.POST['password']
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        if Donor.objects.filter(email=email).exists():
            messages.warning(request, "⚠️ Email already registered. Please log in instead.")
            return redirect('donor_login')

        donor = Donor.objects.create(
            name=name, email=email, phone=phone, age=age, gender=gender,
            blood_group=blood_group, state=state, district=district,
            location=location, password=hashed_pw, is_verified=True
        )
        request.session['donor_email'] = donor.email
        return redirect('donor_profile')
    return render(request, 'donor_register.html')


def donor_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        if not email or not password:
            messages.error(request, "Please enter email and password.")
            return render(request, 'donor_login.html')

        # Hash the entered password
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        try:
            donor = Donor.objects.get(email=email, password=hashed_pw)
            # Successful login
            request.session['donor_email'] = donor.email
            messages.success(request, "Logged in successfully!")
            return redirect('donor_profile')
        except Donor.DoesNotExist:
            messages.error(request, "❌ Invalid email or password.")

    return render(request, 'donor_login.html')

def donor_logout(request):
    request.session.pop('donor_email', None)
    logout(request)
    return redirect('donor_login')


# views.py
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Donor, Donation, DonorRequest

def donor_profile(request):
    if 'donor_email' not in request.session:
        return redirect('donor_login')

    donor = get_object_or_404(Donor, email=request.session['donor_email'])
    donation_list = Donation.objects.filter(donor=donor).order_by('-date')
    donation_count = donation_list.count()
    last_donation = donation_list.first()
    donor_requests = DonorRequest.objects.filter(donor_name=donor.name).order_by('-created_at')

    # 🩸 Milestone tracking
    milestone_5 = donation_count >= 5
    milestone_10 = donation_count >= 10

    # 🩸 Cooldown Tracking (90 days)
    last_donation_date = last_donation.date if last_donation else None
    eligible = True
    next_eligible = None

    if last_donation_date:
        next_eligible = last_donation_date + timedelta(days=90)
        eligible = timezone.now().date() >= next_eligible

    # Optional: Auto-update donor.last_donation_date field
    if last_donation_date and donor.last_donation_date != last_donation_date:
        donor.last_donation_date = last_donation_date
        donor.save(update_fields=['last_donation_date'])

    # Optional: Show notification when re-eligible
    if not eligible:
        days_left = (next_eligible - timezone.now().date()).days
        messages.info(request, f"You can donate again in {days_left} days (on {next_eligible}).")

    return render(request, 'donor_profile.html', {
        'donor': donor,
        'donation_list': donation_list,
        'donation_count': donation_count,
        'last_donation': last_donation_date,
        'milestone_5': milestone_5,
        'milestone_10': milestone_10,
        'donor_requests': donor_requests,
        'eligible': eligible,
        'next_eligible': next_eligible,
    })



def edit_donor_profile(request):
    donor_email = request.session.get('donor_email')
    if not donor_email:
        return redirect('donor_login')
    
    donor = get_object_or_404(Donor, email=donor_email)
    
    if request.method == "POST":
        donor.name = request.POST.get('name', donor.name)
        donor.email = request.POST.get('email', donor.email)
        donor.phone = request.POST.get('phone', donor.phone)
        donor.state = request.POST.get('state', donor.state)
        donor.district = request.POST.get('district', donor.district)
        donor.location = request.POST.get('location', donor.location)
        donor.gender = request.POST.get('gender', donor.gender)
        donor.age = request.POST.get('age', donor.age)
        donor.blood_group = request.POST.get('blood_group', donor.blood_group)

        # Handle password change
        new_password = request.POST.get('password')
        if new_password:
            donor.password = hashlib.sha256(new_password.encode()).hexdigest()

        # Handle profile photo upload
        if request.FILES.get('profile_pic'):
            donor.profile_pic = request.FILES['profile_pic']

        # Handle profile photo removal
        remove_photo = request.POST.get('remove_photo') == '1'
        if remove_photo and donor.profile_pic:
            donor.profile_pic.delete(save=False)
            donor.profile_pic = None
        
        donor.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('donor_profile')
    
    return render(request, 'edit_donor_profile.html', {'donor': donor})


# Delete donor account

def delete_donor(request, donor_id):
    donor = get_object_or_404(Donor, id=donor_id)
    if request.method == 'POST':
        donor.delete()
        messages.success(request, "Your account has been deleted successfully.")
        return redirect('home')  # Redirect to home page or login page
    return redirect('donor_profile')

def verify_donor_email(request, token):
    try:
        donor = Donor.objects.get(verification_token=token)
        donor.is_verified = True
        donor.save()
        return render(request, 'donor_login.html', {'success': '✅ Your email has been verified. You can now log in.'})
    except Donor.DoesNotExist:
        return render(request, 'donor_login.html', {'error': '❌ Invalid or expired verification link.'})


# ==============================
# Blood Requests
# ==============================
def request_blood(request):
    if request.method == "POST":
        patient_name = request.POST.get('patient_name', '').strip()
        hospital_name = request.POST.get('hospital_name', '').strip()
        blood_group_needed = request.POST.get('blood_group_needed', '').strip()
        state = request.POST.get('state', '').strip()
        district = request.POST.get('district', '').strip()
        location = request.POST.get('location', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        age = request.POST.get('age', '').strip()
        gender = request.POST.get('gender', '').strip()
        urgent = request.POST.get('urgent') == 'on'

        if not (patient_name and hospital_name and blood_group_needed and state and district and contact_number and age and gender):
            messages.warning(request, "⚠️ Please fill in all required fields.")
            return render(request, 'request_blood.html')

        # Save urgent properly
        BloodRequest.objects.create(
            patient_name=patient_name,
            hospital_name=hospital_name,
            blood_group_needed=blood_group_needed,
            state=state,
            district=district,
            location=location,
            contact_number=contact_number,
            age=int(age),
            gender=gender,
            urgent=urgent 
        )
        messages.success(request, "✅ Blood request submitted successfully!")
        return redirect('request_blood')

    return render(request, 'request_blood.html')



from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import BloodRequest

def blood_requests_list(request):
    # Only requests from the last 24 hours
    recent_time = timezone.now() - timedelta(hours=24)
    requests_qs = BloodRequest.objects.filter(created_at__gte=recent_time)
    
    # Filters
    blood_group = request.GET.get('blood_group')
    state = request.GET.get('state')
    district = request.GET.get('district')

    if blood_group:
        requests_qs = requests_qs.filter(blood_group_needed__iexact=blood_group)
    if state:
        requests_qs = requests_qs.filter(state__iexact=state)
    if district:
        requests_qs = requests_qs.filter(district__iexact=district)

    # Order: urgent first, then newest
    requests_qs = requests_qs.order_by('-urgent', '-created_at')

    return render(request, 'blood_requests_list.html', {'requests': requests_qs})



def add_blood_request(request):
    if 'hospital_email' not in request.session:
        return redirect('hospital_login')
    hospital = get_object_or_404(Hospital, email=request.session['hospital_email'])
    if request.method == "POST":
        patient_name = request.POST.get('patient_name')
        blood_group_needed = request.POST.get('blood_group_needed')
        location = request.POST.get('location')
        contact_number = request.POST.get('contact_number')
        state = request.POST.get('state')
        district = request.POST.get('district')
        BloodRequest.objects.create(
            patient_name=patient_name,
            hospital_name=hospital.name,
            blood_group_needed=blood_group_needed,
            location=location,
            contact_number=contact_number,
            state=state,
            district=district
        )
        messages.success(request, "Blood request added successfully!")
        return redirect('hospital_profile')
    return render(request, 'add_blood_request.html')


#blood_stock_view

def live_stock(request):
    stocks = BloodStock.objects.all().order_by('blood_group')
    return render(request, 'live_stock.html', {'stocks': stocks})

#Blood stock management by hospital

def manage_blood_stock(request):
    if 'hospital_email' not in request.session:
        return redirect('hospital_login')

    hospital = Hospital.objects.get(email=request.session['hospital_email'])
    stocks = BloodStock.objects.filter(hospital=hospital)

    blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']  # 👈 add this

    if request.method == 'POST':
        blood_type = request.POST.get('blood_type')
        units = request.POST.get('units')
        expiry_date = request.POST.get('expiry_date')

        stock, created = BloodStock.objects.get_or_create(
            hospital=hospital,
            blood_type=blood_type,
            defaults={'units': units, 'expiry_date': expiry_date}
        )

        if not created:
            stock.units = units
            stock.expiry_date = expiry_date
            stock.save()

        messages.success(request, "Blood stock updated successfully!")
        return redirect('manage_blood_stock')

    # 👇 Add blood_types in context
    return render(request, 'manage_blood_stock.html', {
        'hospital': hospital,
        'stocks': stocks,
        'blood_types': blood_types
    })

#delete stock

from django.http import JsonResponse

def delete_blood_stock(request, stock_id):
    if 'hospital_email' not in request.session:
        return redirect('hospital_login')

    try:
        stock = BloodStock.objects.get(id=stock_id)
        stock.delete()
        messages.success(request, "Stock entry deleted successfully.")
    except BloodStock.DoesNotExist:
        messages.error(request, "Stock not found.")

    return redirect('manage_blood_stock')

# ---- Public view (already likely exists in your hospital_public_profile) ----
def hospital_public_profile(request, hospital_id):
    hospital = get_object_or_404(Hospital, id=hospital_id)
    stocks = BloodStock.objects.filter(hospital=hospital)
    return render(request, 'hospital_public_profile.html', {'hospital': hospital, 'stocks': stocks})


# ==============================
# Donor Health / Eligibility
# ==============================
def check_eligibility(health_check):
    if health_check.age < 18 or health_check.age > 65: return False
    if health_check.weight < 50: return False
    if health_check.hemoglobin_level < 12.5: return False
    if (health_check.recent_illness or health_check.medication or health_check.alcohol_24h or
        health_check.smoking or health_check.tattoo_6m or health_check.surgery_6m or
        health_check.chronic_disease or health_check.pregnant or health_check.covid_recent or
        health_check.travel_malaria):
        return False
    return True


def detailed_health_check(request):
    numeric_fields = ['age', 'weight', 'hemoglobin_level']
    yesno_fields = [
        'recent_illness', 'medication', 'alcohol_24h', 'smoking',
        'tattoo_6m', 'surgery_6m', 'chronic_disease', 'pregnant',
        'covid_recent', 'travel_malaria', 'high_blood_pressure', 'diabetes',
        'heart_disease', 'iron_deficiency', 'infectious_disease',
        'recent_dental', 'recent_vaccination', 'recent_piercing'
    ]

    if request.method == "POST":
        form = DetailedHealthCheckForm(request.POST)
        if form.is_valid():
            health_check = form.save(commit=False)
            if request.user.is_authenticated and hasattr(request.user, "donor"):
                health_check.donor = request.user.donor
            health_check.eligible = check_eligibility(health_check)
            if health_check.donor:
                health_check.save()
            return render(
                request,
                "eligible.html" if health_check.eligible else "not_eligible.html",
                {"donor": getattr(health_check, "donor", None), "check": health_check},
            )
        else:
            return render(request, "not_eligible.html", {"errors": form.errors})
    else:
        form = DetailedHealthCheckForm()

    return render(
        request,
        "detailed_health_check.html",
        {
            "form": form,
            "numeric_fields": numeric_fields,
            "yesno_fields": yesno_fields,
        },
    )


# ==============================
# Hospital Registration & Login
# ==============================
def hospital_register(request):
    if request.method == "POST":
        name = request.POST.get('name').strip()
        email = request.POST.get('email').strip()
        phone = request.POST.get('phone').strip()
        location = request.POST.get('location').strip()
        password = request.POST.get('password')
        if Hospital.objects.filter(email=email).exists():
            return render(request, 'hospital_register.html', {'hospital_names': HOSPITAL_NAMES, 'error': 'Email already registered'})
        hospital = Hospital(name=name, email=email, phone=phone, location=location)
        if hasattr(hospital, 'set_password'):
            hospital.set_password(password)
        else:
            hospital.password = password
        hospital.save()
        return redirect('hospital_login')
    return render(request, 'hospital_register.html', {'hospital_names': HOSPITAL_NAMES})


def hospital_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            hospital = Hospital.objects.get(email=email)
            if hospital.check_password(password):
                request.session['hospital_email'] = hospital.email
                return redirect('hospital_profile')
            else:
                messages.error(request, "Invalid password")
        except Hospital.DoesNotExist:
            messages.error(request, "Hospital not found")
        return redirect('hospital_login')
    return render(request, 'hospital_login.html')


def hospital_logout(request):
    request.session.pop('hospital_email', None)
    return redirect('home')


# ==============================
# Hospital Profile & Requests
# ==============================
def hospital_profile(request):
    if 'hospital_email' not in request.session:
        return redirect('hospital_login')
    hospital = get_object_or_404(Hospital, email=request.session['hospital_email'])
    donor_requests = hospital.donor_requests.all().order_by('-created_at')
    return render(request, 'hospital_profile.html', {'hospital': hospital, 'donor_requests': donor_requests})


def edit_hospital_profile(request):
    if 'hospital_email' not in request.session:
        return redirect('hospital_login')
    hospital = get_object_or_404(Hospital, email=request.session['hospital_email'])
    if request.method == "POST":
        hospital.name = request.POST.get('name')
        hospital.phone = request.POST.get('phone')
        hospital.location = request.POST.get('location')
        new_password = request.POST.get('password')
        if new_password: hospital.set_password(new_password)
        hospital.save()
        messages.success(request, "Profile updated successfully")
        return redirect('hospital_profile')
    return render(request, 'edit_hospital_profile.html', {'hospital': hospital})


def hospital_dashboard(request):
    hospitals = Hospital.objects.all()
    return render(request, 'hospital_dashboard.html', {'hospitals': hospitals})


def hospital_list(request):
    hospitals = Hospital.objects.all()
    return render(request, 'hospital_list.html', {'hospitals': hospitals})


def hospital_requests_view(request):
    hospital_email = request.session.get("hospital_email")  
    if not hospital_email: return redirect("hospital_login")
    hospital = get_object_or_404(Hospital, email=hospital_email)
    requests = hospital.donor_requests.all().order_by('-created_at')
    return render(request, "hospital_requests.html", {"hospital": hospital, "requests": requests})


# ==============================
# Donor Request Actions (Accept / Reject)
# ==============================
@require_POST
def accept_request(request, req_id):
    if 'hospital_email' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('hospital_login')
    req = get_object_or_404(DonorRequest, id=req_id, hospital__email=request.session['hospital_email'])
    req.status = "Accepted"
    req.updated_at = timezone.now()
    req.save()
    messages.success(request, f"Request from {req.donor_name} accepted.")
    return redirect("hospital_profile")


@require_POST
def reject_request(request, req_id):
    if 'hospital_email' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('hospital_login')
    req = get_object_or_404(DonorRequest, id=req_id, hospital__email=request.session['hospital_email'])
    req.status = "Rejected"
    req.updated_at = timezone.now()
    req.save()
    messages.success(request, f"Request from {req.donor_name} rejected.")
    return redirect("hospital_profile")


# ==============================
# Donor Request Form (Hospital side)
# ==============================
def donor_request_view(request, hospital_id):
    hospital = get_object_or_404(Hospital, id=hospital_id)
    if request.method == 'POST':
        form = HospitalDonationRequestForm(request.POST)
        if form.is_valid():
            donor_request = form.save(commit=False)
            donor_request.hospital = hospital
            donor_request.status = 'Pending'
            donor_request.save()
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            if not User.objects.filter(username=email).exists():
                User.objects.create_user(username=email, email=email, password=password)
            if not Donor.objects.filter(email=email).exists():
                Donor.objects.create(
                    name=form.cleaned_data.get('donor_name'),
                    email=email,
                    phone=form.cleaned_data.get('donor_contact'),
                    blood_group=form.cleaned_data.get('donor_blood_group'),
                    password=hashlib.sha256(password.encode()).hexdigest(),
                    is_verified=True
                )
            messages.success(request, "Request submitted successfully! You can now log in as a donor.")
            return redirect('donor_request', hospital_id=hospital.id)
    else:
        form = HospitalDonationRequestForm()
    return render(request, 'hospital_request.html', {'form': form, 'hospital': hospital})


# ==============================
# Feedback views
# ==============================

def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('feedback')
    else:
        form = FeedbackForm()
    return render(request, 'feedback.html', {'form': form})