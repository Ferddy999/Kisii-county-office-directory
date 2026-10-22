from django import forms

from .models import Office


class OfficeForm(forms.ModelForm):
    class Meta:
        model = Office
        fields = [
            "name",
            "department",
            "directorate",
            "building",
            "floor_room",
            "phone_ext",
            "email",
            "services",
            "is_active",
        ]
        widgets = {"services": forms.CheckboxSelectMultiple}
        labels = {
            "floor_room": "Floor or room",
            "phone_ext": "Phone extension",
            "email": "Official email",
            "is_active": "Active (shown in the directory)",
        }
        help_texts = {
            "directorate": "Optional. Must belong to the selected department.",
            "phone_ext": "Digits only. Must be unique within the building.",
        }

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_phone_ext(self):
        ext = self.cleaned_data["phone_ext"].strip()
        if ext and not ext.isdigit():
            raise forms.ValidationError("Use digits only, for example 2104.")
        return ext

    def clean(self):
        cleaned = super().clean()
        building = cleaned.get("building")
        ext = cleaned.get("phone_ext")
        if building and ext:
            clash = Office.objects.filter(building__iexact=building, phone_ext=ext)
            if clash.exclude(pk=self.instance.pk).exists():
                self.add_error("phone_ext", "This extension is already used in that building.")
        return cleaned
