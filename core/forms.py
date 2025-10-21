from django import forms
from .models import DonorHealthCheck


class DetailedHealthCheckForm(forms.ModelForm):
    class Meta:
        model = DonorHealthCheck
        exclude = ['donor', 'eligible', 'checked_at']
        widgets = {
            'age': forms.NumberInput(attrs={'min': 18, 'max': 65, 'class': 'border rounded-lg p-2 w-full'}),
            'weight': forms.NumberInput(attrs={'min': 45, 'class': 'border rounded-lg p-2 w-full'}),
            'hemoglobin_level': forms.NumberInput(attrs={'step': 0.1, 'min': 10, 'class': 'border rounded-lg p-2 w-full'}),
            'recent_illness': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'medication': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'chronic_disease': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'high_blood_pressure': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'diabetes': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'heart_disease': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'surgery_6m': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'iron_deficiency': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'infectious_disease': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'recent_dental': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'recent_vaccination': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'alcohol_24h': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'smoking': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'tattoo_6m': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'recent_piercing': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'travel_malaria': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'pregnant': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            'covid_recent': forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
        }

    def clean(self):
        cleaned_data = super().clean()
        age = cleaned_data.get("age")
        weight = cleaned_data.get("weight")
        hemoglobin = cleaned_data.get("hemoglobin_level")

        # Disqualifying factors
        issues = [
            cleaned_data.get("recent_illness"),
            cleaned_data.get("medication"),
            cleaned_data.get("alcohol_24h"),
            cleaned_data.get("smoking"),
            cleaned_data.get("tattoo_6m"),
            cleaned_data.get("surgery_6m"),
            cleaned_data.get("chronic_disease"),
            cleaned_data.get("pregnant"),
            cleaned_data.get("covid_recent"),
            cleaned_data.get("travel_malaria"),
        ]

        if age and (age < 18 or age > 65):
            raise forms.ValidationError("Age must be between 18 and 65.")
        if weight and weight < 50:
            raise forms.ValidationError("Minimum weight should be 50 kg.")
        if hemoglobin and hemoglobin < 12.5:
            raise forms.ValidationError("Hemoglobin must be at least 12.5 g/dL.")

        if any(issues):
            raise forms.ValidationError("You are not eligible to donate at this time due to health reasons.")

        return cleaned_data


from django import forms
from .models import HospitalDonationRequest

class HospitalDonationRequestForm(forms.ModelForm):
    class Meta:
        model = HospitalDonationRequest
        # Exclude hospital and donor, they'll be set automatically in the view
        exclude = ['hospital', 'donor', 'requested_at']
        widgets = {
            'blood_group': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'A+, B-, etc.'
            }),
            'units': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
        }

from django import forms
from .models import DonorRequest

BLOOD_GROUP_CHOICES = [
    ('A+', 'A+'),
    ('A-', 'A-'),
    ('B+', 'B+'),
    ('B-', 'B-'),
    ('AB+', 'AB+'),
    ('AB-', 'AB-'),
    ('O+', 'O+'),
    ('O-', 'O-'),
]

class DonorRequestForm(forms.ModelForm):
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'placeholder': 'Your Email'})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )

    # This is the key change: make donor_blood_group a ChoiceField
    donor_blood_group = forms.ChoiceField(
        choices=BLOOD_GROUP_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = DonorRequest
        fields = ['donor_name', 'donor_age', 'donor_blood_group', 'donor_contact', 'email', 'password']
        widgets = {
            'donor_name': forms.TextInput(attrs={'placeholder': 'Your Full Name'}),
            'donor_age': forms.NumberInput(attrs={'placeholder': 'Your Age'}),
            'donor_contact': forms.TextInput(attrs={'placeholder': 'Contact Number'}),
        }

class HospitalDonationRequestForm(forms.ModelForm):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput(), label="Password")
    
    class Meta:
        model = DonorRequest
        fields = ['donor_name', 'donor_age', 'donor_blood_group', 'donor_contact', 'email', 'password']


#feedback form

from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Your Feedback', 'rows': 4}),
        }
