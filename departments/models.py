from django.db import models

from core.models import TimeStampedModel


class Department(TimeStampedModel):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Directorate(TimeStampedModel):
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="directorates"
    )
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["department__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "name"],
                name="unique_directorate_per_department",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.department.code})"