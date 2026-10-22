import re

from django import forms

from offices.models import Office

from .models import Staff, phone_validator


class StaffForm(forms.ModelForm):
    work_phone = forms.CharField(
        label="Work phone",
        max_length=20,
        help_text="For example 0712 345 678 or +254 712 345 678. Saved as +254712345678.",
    )

    class Meta:
        model = Staff
        fields = [
            "full_name",
            "designation",
            "department",
            "office",
            "work_email",
            "work_phone",
            "is_active",
        ]
        labels = {
            "work_email": "Work email",
            "is_active": "Active (shown in the directory)",
        }
        help_texts = {
            "office": "The office must belong to the selected department.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["office"].queryset = Office.objects.select_related(
            "department"
        ).order_by("name")
        self.fields["office"].label_from_instance = (
            lambda office: f"{office.name} ({office.department.code})"
        )

    def clean_full_name(self):
        return " ".join(self.cleaned_data["full_name"].split())

    def clean_designation(self):
        return " ".join(self.cleaned_data["designation"].split())

    def clean_work_email(self):
        return self.cleaned_data["work_email"].strip().lower()

    def clean_work_phone(self):
        number = re.sub(r"[\s\-().]", "", self.cleaned_data["work_phone"])
        if number.startswith("0"):
            number = "+254" + number[1:]
        elif number.startswith("254"):
            number = "+" + number
        phone_validator(number)
        return number
