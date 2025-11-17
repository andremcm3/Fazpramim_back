from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ClientProfile, ProviderProfile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class ClientSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=255)
    cpf = forms.CharField(max_length=20)
    phone = forms.CharField(max_length=30, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    identity_document = forms.FileField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", 'full_name', 'cpf', 'phone', 'address', 'identity_document')

    def save(self, commit=True):
        user = super().save(commit=commit)
        # create client profile
        ClientProfile.objects.create(
            user=user,
            full_name=self.cleaned_data.get('full_name'),
            cpf=self.cleaned_data.get('cpf'),
            phone=self.cleaned_data.get('phone'),
            address=self.cleaned_data.get('address'),
            identity_document=self.cleaned_data.get('identity_document'),
        )
        return user


class ProviderSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=255)
    professional_email = forms.EmailField(required=True)
    service_address = forms.CharField(widget=forms.Textarea, required=False)
    technical_qualification = forms.CharField(widget=forms.Textarea, required=False)
    identity_document = forms.FileField(required=False)
    certifications = forms.FileField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", 'full_name', 'professional_email', 'service_address', 'technical_qualification', 'identity_document', 'certifications')

    def save(self, commit=True):
        user = super().save(commit=commit)
        ProviderProfile.objects.create(
            user=user,
            full_name=self.cleaned_data.get('full_name'),
            professional_email=self.cleaned_data.get('professional_email'),
            service_address=self.cleaned_data.get('service_address'),
            technical_qualification=self.cleaned_data.get('technical_qualification'),
            identity_document=self.cleaned_data.get('identity_document'),
            certifications=self.cleaned_data.get('certifications'),
        )
        return user
