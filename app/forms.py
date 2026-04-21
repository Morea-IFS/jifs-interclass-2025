from django import forms

class Terms_UseForm(forms.Form):
    terms_accept = forms.BooleanField(label="Eu aceito os Termos de Uso", required=True)