from django import forms


class FlowForm(forms.Form):
    flow_name = forms.CharField(
        max_length=255,
        label="Nome do Fluxo",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ex: Contrato de Prestação de Serviços",
            }
        ),
    )


class DocumentConfigForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        label="Nome do Documento",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    pdf_url = forms.URLField(
        label="URL do PDF",
        widget=forms.URLInput(
            attrs={
                "class": "form-control",
                "placeholder": "https://exemplo.com/contrato.pdf",
            }
        ),
    )
