from django import forms


IMAGE_SIZE_LIMIT = 10 * 1024 * 1024  # 10MB limit for uploaded images


class ImageUploadForm(forms.Form):
    image = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'id': 'file-input',
            'capture': 'environment',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')

        if not image:
            raise forms.ValidationError("Merci de sélectionner une image ou de prendre une photo.")

        # Validate file size
        if image.size > IMAGE_SIZE_LIMIT:
            raise forms.ValidationError("Les fichiers ne doivent pas dépasser 10 Mo.")

        return cleaned_data
