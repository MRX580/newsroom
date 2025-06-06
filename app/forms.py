from django import forms

class StatsFilterForm(forms.Form):
    publication_from = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Публикация c"
    )
    publication_to = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Публикация по"
    )
    operation_from = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Операции c"
    )
    operation_to = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Операции по"
    )
    keyword = forms.CharField(
        max_length=128,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Ключевое слово"
    )
