from django import forms
from .models import Form


class ContactForm(forms.ModelForm):
    class Meta:
        model = Form
        fields = [
            # 'form_name',
            'name',
            'phone',
            # 'email'
        ]

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)

        self.fields['name'].label = False
        self.fields['phone'].label = False


        self.fields['name'].widget.attrs.update({
            'placeholder': "Ваше ім'я",
            'class': 'form-input',
        })
        self.fields['phone'].widget.attrs.update({
            'placeholder': "Ваш телефон",
            'class': 'form-input',
        })

    def as_text(self):
        return (
            # f"Назва: {self.cleaned_data.get('form_name')}\n"
            f"Ім'я: {self.cleaned_data.get('name')}\n"
            f"Телефон: {self.cleaned_data.get('phone')}\n"
            # f"Пошта: {self.cleaned_data.get('email')}"
        )
