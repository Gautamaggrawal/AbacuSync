from django.contrib import admin

from .models import Question, StudentAnswer, StudentTest, Test, TestSection, TestSession


class TestSectionInline(admin.TabularInline):
    model = TestSection
    extra = 1


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("uuid", "id", "title", "level", "duration_minutes", "is_active", "created_at")
    list_filter = ("is_active", "level")
    search_fields = ("title",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    inlines = [TestSectionInline]


@admin.register(TestSection)
class TestSectionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "test", "order", "created_at")
    list_filter = ("test",)
    search_fields = ("title", "test__title")
    ordering = ("test", "order")
    list_editable = ("order",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("uuid", "id", "text", "section", "order", "marks", "created_at")
    list_filter = ("section",)
    search_fields = ("text", "section__title")
    ordering = ("section", "order")
    list_editable = ("order", "marks")


@admin.register(StudentTest)
class StudentTestAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "test", "status", "start_time", "end_time", "score")
    list_filter = ("status", "test")
    search_fields = ("student__name", "test__title")
    ordering = ("-start_time",)
    date_hierarchy = "start_time"
    readonly_fields = ("duration", "is_timed_out")


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "student_test", "question", "is_correct", "marks_obtained", "created_at")
    list_filter = ("is_correct", "student_test__test")
    search_fields = ("student_test__student__name", "question__text")
    ordering = ("-created_at",)


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student_test",
        "session_id",
        "is_active",
        "remaining_time_seconds",
        "last_sync",
    )
    list_filter = ("is_active",)
    search_fields = ("student_test__student__name", "session_id")
    ordering = ("-last_sync",)
