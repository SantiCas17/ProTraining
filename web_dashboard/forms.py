from django import forms
from activities.models import CyclingActivity, RunActivity, SwimActivity

class BaseActivityForm(forms.ModelForm):
    """Clase base para inyectar diseño Dark Mode a todos los inputs"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Evitamos ponerle la clase de texto a los checkboxes
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control bg-dark text-light border-secondary'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control bg-dark text-light border-secondary'

class RunActivityForm(BaseActivityForm):
    class Meta:
        model = RunActivity
        fields = '__all__'
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class BikeActivityForm(BaseActivityForm):
    class Meta:
        model = CyclingActivity
        fields = '__all__'
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class SwimActivityForm(BaseActivityForm):
    class Meta:
        model = SwimActivity
        fields = '__all__'
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }