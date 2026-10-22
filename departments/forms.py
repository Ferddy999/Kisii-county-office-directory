from django import forms

from .models import Department, Directorate


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "code", "description", "is_active"]
        labels = {
            "code": "Short code",
            "is_active": "Active (shown in the directory)",
        }
        help_texts = {
            "code": "Letters and digits only, up to 10, for example FIN. Saved in capitals.",
        }
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        clash = Department.objects.filter(name__iexact=name).exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError("A department with this name already exists.")
        return name

    def clean_code(self):
        code = self.cleaned_data["code"].strip().upper()
        if not code.isalnum():
            raise forms.ValidationError("Use letters and digits only.")
        return code


class DirectorateForm(forms.ModelForm):
    class Meta:
        model = Directorate
        fields = ["department", "name"]

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())

    def clean(self):
        cleaned = super().clean()
        department = cleaned.get("department")
        name = cleaned.get("name")
        if department and name:
            clash = Directorate.objects.filter(department=department, name__iexact=name)
            if clash.exclude(pk=self.instance.pk).exists():
                self.add_error("name", "This department already has a directorate with that name.")
        return cleaned
