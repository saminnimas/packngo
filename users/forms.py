from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from phonenumber_field.formfields import PhoneNumberField
from .models import CustomUser


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Enter a valid email address.')
    phone = PhoneNumberField(help_text='Required. Enter your phone number')

    class Meta: # Creates a nested namespace for the configuration. this includes the effected table / model, order of fields etc
        model = CustomUser # effected model
        fields = ('username', 'email', 'phone', 'password1', 'password2') # order of fields


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(max_length=254, required=False, help_text='Update your email.')
    phone = PhoneNumberField(required=False, help_text='Enter your phone number.')
    expense_threshold = forms.IntegerField(required=False, help_text='Enter expense threshold')
    old_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text='Enter your current password to change it.'
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text='Enter your new password.'
    )
    new_password_again = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text='Confirm new password.'
    )

    class Meta:
        model = CustomUser
        fields = ('expense_threshold', 'email', 'phone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['email'].initial = self.instance.email
            self.fields['phone'].initial = self.instance.phone

    def clean(self):
        cleaned_data = super(UserProfileForm, self).clean()
        old_password = cleaned_data.get('old_password', '')
        new_password = cleaned_data.get('new_password', '')
        new_password_again = cleaned_data.get('new_password_again', '')

        if any([old_password, new_password, new_password_again]):
            if not all([old_password, new_password, new_password_again]):
                raise forms.ValidationError("All password fields are required to change your password.")
            if not self.instance.check_password(old_password):
                self.add_error('old_password', "Your old password is incorrect.")
                raise forms.ValidationError("Your old password is incorrect.")
            if new_password != new_password_again:
                self.add_error('new_password_again', "New passwords do not match.")
                raise forms.ValidationError("New passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        print("self.cleaned_data before save:", self.cleaned_data)
        if self.cleaned_data.get('email'):
            user.email = self.cleaned_data['email']
        if self.cleaned_data.get('phone'):
            user.phone = self.cleaned_data['phone']
        if self.cleaned_data.get('new_password'):
            user.set_password(self.cleaned_data['new_password'])
        if commit:
            user.save()
        print("self.cleaned_data after save:", self.cleaned_data)  # Debug
        return user