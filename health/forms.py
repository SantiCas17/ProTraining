from django import forms
from .models import ErgometryTest

class ErgometryTestForm(forms.ModelForm):
    class Meta:
        model = ErgometryTest
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control bg-dark text-light border-secondary'