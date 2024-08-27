from django import forms
from .models import Form


class ContactForm(forms.ModelForm):
    class Meta:
        model = Form
        fields = ['form_name', 'name', 'phone', 'email']
