from django import forms
from .models import RaceGoal

class RaceGoalForm(forms.ModelForm):
    class Meta:
        model = RaceGoal
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'training_start_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput) and not isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = 'form-control bg-dark text-light border-secondary'
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = 'form-control bg-dark text-light border-secondary border'