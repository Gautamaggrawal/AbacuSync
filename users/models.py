from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from uuid import UUID, uuid4


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, email, password=None, **extra_fields):
        if not phone_number:
            raise ValueError(_("The Phone Number must be set"))
        if not email:
            raise ValueError(_("The Email must be set"))

        email = self.normalize_email(email)
        user = self.model(phone_number=phone_number, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("user_type", "ADMIN")

        return self.create_user(phone_number, email, password, **extra_fields)


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ("ADMIN", "Admin"),
        ("CENTRE", "Centre"),
        ("STUDENT", "Student"),
    )
    uuid = models.UUIDField(
        default=uuid4, unique=True, editable=False, verbose_name=_("UUID")
    )

    username = None
    phone_number = models.CharField(_("phone number"), max_length=15, unique=True)
    email = models.EmailField(_("email address"), unique=True)
    user_type = models.CharField(
        _("user type"), max_length=10, choices=USER_TYPE_CHOICES
    )
    is_superuser = models.BooleanField(
        _("superuser status"),
        default=False,
        db_index=True,
        help_text=_(
            "Designates that this user has all permissions without "
            "explicitly assigning them."
        ),
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        db_index=True,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        db_index=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["email"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        indexes = [
            models.Index(fields=["phone_number"]),
            models.Index(fields=["user_type"]),
        ]

    def __str__(self):
        return self.phone_number


class UUIDManager(models.Manager):
    """Base manager class for models having a `uuid` natural key field."""

    def get_by_natural_key(self, uuid):
        return self.get(uuid=uuid)

    # def analytics(self):
    #     return self.using(settings.ANALYTICS_DATABASE_ALIAS)

    # def readonly(self):
    #     return self.using(settings.READONLY_DATABASE_ALIAS)


class UUIDModel(models.Model):
    """Base model class that has a `uuid` natural key field."""

    uuid = models.UUIDField(
        default=uuid4, unique=True, editable=False, verbose_name=_("UUID")
    )

    objects = UUIDManager()

    class Meta:
        abstract = True

    def natural_key(self):
        return (self.uuid,)
