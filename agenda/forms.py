from django import forms

from . import services


class ConfirmarForm(forms.Form):
    nome = forms.CharField(label="Nome", max_length=80, strip=True)
    telefone = forms.CharField(label="Telefone", max_length=20)

    def clean_telefone(self):
        try:
            return services.normalizar_telefone(self.cleaned_data["telefone"])
        except ValueError as erro:
            raise forms.ValidationError(str(erro))
