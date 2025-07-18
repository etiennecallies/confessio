from django import forms


IMAGE_SIZE_LIMIT = 10 * 1024 * 1024  # 10MB limit for uploaded images


class ImageUploadForm(forms.Form):
    image = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'id': 'file-input'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        print(cleaned_data)
        image = cleaned_data.get('image')

        if not image:
            raise forms.ValidationError("Please select a file or take a picture.")

        # Validate file size
        if image.size > IMAGE_SIZE_LIMIT:
            raise forms.ValidationError("File size cannot exceed 10MB.")

        return cleaned_data
