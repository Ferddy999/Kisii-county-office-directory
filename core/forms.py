from django import forms

from departments.models import Department
from offices.models import Office, Service


class DirectoryFilterForm(forms.Form):
    q = forms.CharField(label="Staff or office name", required=False, max_length=100)
    department = forms.ModelChoiceField(
        label="Department",
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label="All departments",
    )
    office = forms.ModelChoiceField(
        label="Office",
        queryset=Office.objects.filter(is_active=True),
        required=False,
        empty_label="All offices",
    )
    building = forms.ChoiceField(label="Building or location", required=False)
    service = forms.ModelChoiceField(
        label="Service offered",
        queryset=Service.objects.all(),
        required=False,
        empty_label="All services",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        buildings = (
            Office.objects.filter(is_active=True)
            .order_by("building")
            .values_list("building", flat=True)
            .distinct()
        )
        self.fields["building"].choices = [("", "All locations")] + [
            (name, name) for name in buildings
        ]
