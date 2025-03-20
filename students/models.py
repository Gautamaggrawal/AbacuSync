from django.db import models
from django.utils.translation import gettext_lazy as _

from centres.models import CI, Centre
from users.models import User, UUIDModel


class Level(UUIDModel):
    """Student levels"""

    name = models.CharField(_("name"), max_length=50)
    description = models.TextField(_("description"), blank=True, null=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("level")
        verbose_name_plural = _("levels")

    def __str__(self):
        return self.name


class Student(UUIDModel):
    GENDER_CHOICES = (
        ("M", _("Male")),
        ("F", _("Female")),
        ("O", _("Other")),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
        help_text=_("User account associated with this student"),
    )
    centre = models.ForeignKey(
        Centre,
        on_delete=models.CASCADE,
        related_name="students",
        help_text=_("Centre this student belongs to"),
    )
    name = models.CharField(_("name"), max_length=100)
    dob = models.DateField(_("date of birth"))
    gender = models.CharField(_("gender"), max_length=1, choices=GENDER_CHOICES)
    current_level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name="students",
        help_text=_("Current level of the student"),
    )
    ci = models.ForeignKey(
        CI,
        on_delete=models.CASCADE,
        related_name="students",
        help_text=_("CI assigned to this student"),
        null=True, blank=True
    )
    level_start_date = models.DateField(_("level start date"))
    level_completion_date = models.DateField(_("level completion date"), null=True, blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("student")
        verbose_name_plural = _("students")
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["centre", "is_active"]),
        ]

    def __str__(self):
        return self.name


class StudentLevelHistory(UUIDModel):
    """Track student level changes"""

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="level_history",
        help_text=_("Student whose level is being changed"),
    )
    previous_level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name="previous_students",
        null=True,
        blank=True,
        help_text=_("Previous level of the student"),
    )
    new_level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name="new_students",
        help_text=_("New level of the student"),
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="level_changes",
        help_text=_("User who changed the level"),
    )
    start_date = models.DateField(_("start date"))
    completion_date = models.DateField(_("completion date"), auto_now_add=True, null=True, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("student level history")
        verbose_name_plural = _("student level histories")
        indexes = [
            models.Index(fields=["student", "created_at"]),
        ]

    def __str__(self):
        return f"{self.student.name} - {self.previous_level} to {self.new_level}"
