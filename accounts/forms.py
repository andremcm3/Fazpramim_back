from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ClientProfile, ProviderProfile
from .models import ServiceRequest



class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user



class ClientSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=255)
    cpf = forms.CharField(max_length=20)
    phone = forms.CharField(max_length=30, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    city = forms.CharField(max_length=100, required=False)
    state = forms.CharField(max_length=100, required=False)
    profile_photo = forms.ImageField(required=False)
    identity_document = forms.FileField(required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "full_name",
            "cpf",
            "phone",
            "address",
            "city",
            "state",
            "profile_photo",
            "identity_document",
        )

    def save(self, commit=True):
        
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()

        
        ClientProfile.objects.create(
            user=user,
            full_name=self.cleaned_data.get("full_name"),
            cpf=self.cleaned_data.get("cpf"),
            phone=self.cleaned_data.get("phone"),
            address=self.cleaned_data.get("address"),
            city=self.cleaned_data.get("city"),
            state=self.cleaned_data.get("state"),
            profile_photo=self.cleaned_data.get("profile_photo"),
            identity_document=self.cleaned_data.get("identity_document"),
        )
        return user



class ProviderSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=255)
    professional_email = forms.EmailField(required=True)
    service_address = forms.CharField(widget=forms.Textarea, required=False)
    technical_qualification = forms.CharField(
        widget=forms.Textarea,
        required=False,
    )
    profile_photo = forms.ImageField(required=False)
    identity_document = forms.FileField(required=False)
    certifications = forms.FileField(required=False)
    city = forms.CharField(max_length=100, required=False)
    state = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "full_name",
            "professional_email",
            "service_address",
            "city",
            "state",
            "technical_qualification",
            "profile_photo",
            "identity_document",
            "certifications",
        )

    def save(self, commit=True):
  
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()

    
        ProviderProfile.objects.create(
            user=user,
            full_name=self.cleaned_data.get("full_name"),
            professional_email=self.cleaned_data.get("professional_email"),
            service_address=self.cleaned_data.get("service_address"),
            city=self.cleaned_data.get("city"),
            state=self.cleaned_data.get("state"),
            technical_qualification=self.cleaned_data.get("technical_qualification"),
            profile_photo=self.cleaned_data.get("profile_photo"),
            identity_document=self.cleaned_data.get("identity_document"),
            certifications=self.cleaned_data.get("certifications"),
        )
        return user



class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        fields = ["full_name", "cpf", "phone", "address", "city", "state", "profile_photo", "identity_document"]


class ProviderProfileForm(forms.ModelForm):
    class Meta:
        model = ProviderProfile
        fields = [
            "full_name",
            "professional_email",
            "service_address",
            "city",
            "state",
            "technical_qualification",
            "profile_photo",
            "identity_document",
            "certifications",
        ]


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ["description", "desired_datetime", "proposed_value"]
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 5,
                "required": True,
                "placeholder": "Descreva detalhadamente o serviço que você precisa...",
                "style": "width:100%; min-height:120px; box-sizing:border-box; padding:8px; background:#fff; color:#000; border:1px solid #ccc; border-radius:4px;"
            }),
            "desired_datetime": forms.DateTimeInput(attrs={"type": "datetime-local", "style": "display:block; width:100%; box-sizing:border-box; padding:6px;"}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proposed_value'].widget.attrs.update({
            'step': '0.01',
            'placeholder': '150.00',
            'style': 'display:block; width:200px; box-sizing:border-box; padding:6px;'
        })
