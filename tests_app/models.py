import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from students.models import Level, Student
from users.models import UUIDModel


class Test(UUIDModel):
    """Test model"""

    title = models.CharField(_("title"), max_length=200)
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name="tests",
        help_text=_("Level this test is designed for"),
    )
    due_date = models.DateTimeField(_("Due date"), null=True, blank=True)
    duration_minutes = models.IntegerField(_("duration (minutes)"), default=8)
    is_active = models.BooleanField(_("active"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("test")
        verbose_name_plural = _("tests")
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["level", "is_active"]),
        ]

    def __str__(self):
        return self.title


class TestSection(UUIDModel):
    """Test sections"""

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name="sections",
        help_text=_("Test this section belongs to"),
    )
    section_type = models.CharField(_("Section Type"), max_length=100)
    order = models.IntegerField(_("order"))
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("test section")
        verbose_name_plural = _("test sections")
        ordering = ["order"]
        indexes = [
            models.Index(fields=["test", "order"]),
        ]

    def __str__(self):
        return f"{self.section_type}"


class Question(UUIDModel):
    """Questions for tests"""

    class QuestionType(models.TextChoices):
        """Enum for different types of questions"""

        PLUS = "plus", _("Plus/Addition")
        MULTIPLY = "multiply", _("Multiply")
        DIVIDE = "divide", _("Divide/Division")

    section = models.ForeignKey(
        TestSection,
        on_delete=models.CASCADE,
        related_name="questions",
        help_text=_("Section this question belongs to"),
    )
    text = models.TextField(_("question text"))
    order = models.IntegerField(_("order"))
    marks = models.IntegerField(_("marks"), default=1)
    question_type = models.CharField(
        _("question type"),
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.PLUS,
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("question")
        verbose_name_plural = _("questions")
        ordering = ["order"]
        indexes = [models.Index(fields=["section", "question_type", "order"])]

    def __str__(self):
        return f"Question {self.order} - {self.section.test.title}"


class StudentTest(UUIDModel):
    """Record of tests taken by students"""

    STATUS_CHOICES = (
        ("PENDING", _("Pending")),
        ("IN_PROGRESS", _("In Progress")),
        ("COMPLETED", _("Completed")),
        ("INTERRUPTED", _("Interrupted")),
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="tests",
        help_text=_("Student taking the test"),
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name="student_tests",
        help_text=_("Test being taken"),
    )
    status = models.CharField(
        _("status"), max_length=20, choices=STATUS_CHOICES, default="PENDING"
    )
    start_time = models.DateTimeField(_("start time"), null=True, blank=True)
    end_time = models.DateTimeField(_("end time"), null=True, blank=True)
    score = models.DecimalField(
        _("score"), max_digits=5, decimal_places=2, null=True, blank=True
    )
    current_section = models.ForeignKey(
        TestSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="in_progress_tests",
        help_text=_("Current section the student is working on"),
    )
    last_activity = models.DateTimeField(_("last activity"), auto_now=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("student test")
        verbose_name_plural = _("student tests")
        indexes = [
            models.Index(fields=["student", "status"]),
            models.Index(fields=["status", "start_time"]),
            models.Index(fields=["test", "status"]),
        ]

    def __str__(self):
        return f"{self.student.name} - {self.test.title}"

    @property
    def duration(self):
        """Calculate test duration in minutes"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return None

    @property
    def is_timed_out(self):
        """Check if test has timed out"""
        if self.start_time and self.status == "IN_PROGRESS":
            elapsed = (timezone.now() - self.start_time).total_seconds() / 60
            return elapsed >= self.test.duration_minutes
        return False

    def save(self, *args, **kwargs):
        """Override save to set end_time when test is completed"""
        if self.status == "COMPLETED" and not self.end_time:
            self.end_time = timezone.now()
        super().save(*args, **kwargs)


class StudentAnswer(UUIDModel):
    """Student answers for test questions"""

    student_test = models.ForeignKey(
        StudentTest,
        on_delete=models.CASCADE,
        related_name="answers",
        help_text=_("Test this answer belongs to"),
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="student_answers",
        help_text=_("Question being answered"),
    )
    answer_text = models.TextField(_("answer text"), blank=True, null=True)
    is_correct = models.BooleanField(_("is correct"), null=True, blank=True)
    marks_obtained = models.DecimalField(
        _("marks obtained"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("student answer")
        verbose_name_plural = _("student answers")
        unique_together = ["student_test", "question"]
        indexes = [
            models.Index(fields=["student_test", "question"]),
            models.Index(fields=["is_correct"]),
        ]

    def __str__(self):
        return f"{self.student_test.student.name} - {self.question}"


class TestSession(UUIDModel):
    """Tracks test session status for handling interruptions and resumptions"""

    student_test = models.OneToOneField(
        StudentTest,
        on_delete=models.CASCADE,
        related_name="session",
        help_text=_("Test this session belongs to"),
    )
    session_id = models.UUIDField(
        _("session ID"), default=uuid.uuid4, editable=False
    )
    last_question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
        help_text=_("Last question the student was working on"),
    )
    is_active = models.BooleanField(_("active"), default=True)
    remaining_time_seconds = models.IntegerField(
        _("remaining time (seconds)"), null=True, blank=True
    )
    last_sync = models.DateTimeField(_("last sync"), auto_now=True)

    class Meta:
        verbose_name = _("test session")
        verbose_name_plural = _("test sessions")
        indexes = [
            models.Index(fields=["session_id"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"Session for {self.student_test.student.name} - {self.student_test.test.title}"
