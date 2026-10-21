from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from core.models import TimeStampedModel
from departments.models import Department
from offices.models import Office

phone_validator = RegexValidator(
    regex=r"^\+254\d{9}$",
    message="Enter the number as +254 followed by 9 digits, e.g. +254712345678.",
)


class Staff(TimeStampedModel):
    full_name = models.CharField(max_length=150, db_index=True)
    designation = models.CharField(max_length=150)
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="staff_members"
    )
    office = models.ForeignKey(
        Office, on_delete=models.PROTECT, related_name="staff_members"
    )
    work_email = models.EmailField(unique=True)
    work_phone = models.CharField(
        max_length=13, unique=True, validators=[phone_validator]
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["full_name"]
        verbose_name_plural = "staff"

    def __str__(self):
        return self.full_name

    def clean(self):
        if self.office_id and self.office.department_id != self.department_id:
            raise ValidationError(
                {"office": "This office belongs to a different department."}
            )