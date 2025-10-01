from django import forms
from .models import Workflow
import json


class WorkflowAdminForm(forms.ModelForm):
    preview_images_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Her satıra bir resim URL'si yazın veya virgülle ayırın"
    )
    tags_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        help_text="Tag'leri virgülle ayırın: automation,email,marketing"
    )
    n8n_workflow_json = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 10}),
        help_text="N8N workflow JSON verisini buraya yapıştırın"
    )

    class Meta:
        model = Workflow
        exclude = ['preview_images', 'tags', 'n8n_workflow_data']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Mevcut verileri string formatına çevir
            if self.instance.preview_images:
                self.fields['preview_images_text'].initial = ','.join(self.instance.preview_images)

            if self.instance.tags:
                self.fields['tags_text'].initial = ','.join(self.instance.tags)

            if self.instance.n8n_workflow_data:
                self.fields['n8n_workflow_json'].initial = json.dumps(
                    self.instance.n8n_workflow_data, indent=2
                )

    def clean_n8n_workflow_json(self):
        value = self.cleaned_data.get('n8n_workflow_json')
        if value:
            try:
                json.loads(value)
                return value
            except json.JSONDecodeError:
                raise forms.ValidationError("Geçersiz JSON formatı")
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)

        # String verilerini JSON'a çevir
        preview_images_text = self.cleaned_data.get('preview_images_text')
        if preview_images_text:
            # Hem virgül hem de yeni satır ile ayırma
            images = []
            for line in preview_images_text.split('\n'):
                for img in line.split(','):
                    img = img.strip()
                    if img:
                        images.append(img)
            instance.preview_images = images
        else:
            instance.preview_images = []

        tags_text = self.cleaned_data.get('tags_text')
        if tags_text:
            tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
            instance.tags = tags
        else:
            instance.tags = []

        n8n_workflow_json = self.cleaned_data.get('n8n_workflow_json')
        if n8n_workflow_json:
            instance.n8n_workflow_data = json.loads(n8n_workflow_json)
        else:
            instance.n8n_workflow_data = {}

        if commit:
            instance.save()
        return instance