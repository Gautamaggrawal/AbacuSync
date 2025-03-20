# centres/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User, UUIDModel


class Centre(UUIDModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="centre_profile")
    centre_name = models.CharField(max_length=100)
    franchisee_name = models.CharField(max_length=100)
    area = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("centre")
        verbose_name_plural = _("centres")
        indexes = [
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.centre_name


class CI(UUIDModel):
    """CI (Counselor/Instructor) model"""

    name = models.CharField(_("name"), max_length=100)
    centre = models.ForeignKey(
        Centre,
        on_delete=models.CASCADE,
        related_name="cis",
        help_text=_("Centre this CI belongs to"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("CI")
        verbose_name_plural = _("CIs")

    def __str__(self):
        return f"{self.name} - {self.centre.centre_name}"
