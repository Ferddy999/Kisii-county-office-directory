from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from core.models import TimeStampedModel
from departments.models import Department, Directorate


class Service(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Office(TimeStampedModel):
    name = models.CharField(max_length=200, db_index=True)
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="offices"
    )
    directorate = models.ForeignKey(
        Directorate,
        on_delete=models.PROTECT,
        related_name="offices",
        null=True,
        blank=True,
    )
    building = models.CharField(max_length=100)
    floor_room = models.CharField(max_length=50, blank=True)
    phone_ext = models.CharField(max_length=10, blank=True)
    email = models.EmailField(unique=True)
    services = models.ManyToManyField(Service, blank=True, related_name="offices")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "name"],
                name="unique_office_per_department",
            ),
            models.UniqueConstraint(
                fields=["building", "phone_ext"],
                condition=~Q(phone_ext=""),
                name="unique_extension_per_building",
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.directorate_id and self.directorate.department_id != self.department_id:
            raise ValidationError(
                {"directorate": "This directorate belongs to a different department."}
            )