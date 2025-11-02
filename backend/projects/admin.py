from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Feature,
    Project,
    QualityAttributeCategory,
    QualityAttributeScenario,
    Requirement,
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "tenant",
        "created_by",
        "is_active",
        "feature_count",
        "created_at",
    ]
    list_filter = ["is_active", "created_at", "tenant"]
    search_fields = ["name", "slug", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "tenant",
                    "name",
                    "slug",
                    "description",
                    "is_active",
                )
            },
        ),
        (
            "Metadata",
            {"fields": ("created_by", "created_at", "updated_at")},
        ),
    )
    list_per_page = 25

    def feature_count(self, obj):
        """Display number of features in this project"""
        if obj.pk:
            count = obj.features.count()
            return format_html(
                '<a href="/admin/projects/feature/?project__id__exact={}">{}</a>',
                obj.id,
                count,
            )
        return 0

    feature_count.short_description = "Features"


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "project",
        "feature_type",
        "parent",
        "status",
        "priority",
        "requirement_count",
        "created_at",
    ]
    list_filter = [
        "feature_type",
        "status",
        "created_at",
        "project",
        "tenant",
    ]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "tenant",
                    "project",
                    "parent",
                    "title",
                    "description",
                )
            },
        ),
        (
            "Classification",
            {"fields": ("feature_type", "status", "priority")},
        ),
        (
            "Metadata",
            {"fields": ("created_by", "created_at", "updated_at")},
        ),
    )
    list_per_page = 25

    def requirement_count(self, obj):
        """Display number of requirements for this feature"""
        if obj.pk:
            count = obj.requirements.count()
            return format_html(
                '<a href="/admin/projects/requirement/?feature__id__exact={}">{}</a>',
                obj.id,
                count,
            )
        return 0

    requirement_count.short_description = "Requirements"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("project", "parent")


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "feature",
        "requirement_type",
        "is_satisfied",
        "priority",
        "created_at",
    ]
    list_filter = [
        "requirement_type",
        "is_satisfied",
        "created_at",
        "feature__project",
        "tenant",
    ]
    search_fields = ["title", "description", "acceptance_criteria"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "tenant",
                    "feature",
                    "title",
                    "description",
                    "requirement_type",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "acceptance_criteria",
                    "priority",
                    "is_satisfied",
                )
            },
        ),
        (
            "Metadata",
            {"fields": ("created_by", "created_at", "updated_at")},
        ),
    )
    list_per_page = 25

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related("feature", "feature__project")
        )


@admin.register(QualityAttributeCategory)
class QualityAttributeCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "order", "quality_attribute_count"]
    list_filter = ["parent", "tenant"]
    search_fields = ["name", "description"]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "tenant",
                    "parent",
                    "name",
                    "description",
                    "order",
                )
            },
        ),
    )

    def quality_attribute_count(self, obj):
        """Display number of quality attributes in this category"""
        if obj.pk:
            return obj.quality_attributes.count()
        return 0

    quality_attribute_count.short_description = "Quality Attributes"


@admin.register(QualityAttributeScenario)
class QualityAttributeScenarioAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "feature",
        "category",
        "is_critical",
        "priority",
        "created_at",
    ]
    list_filter = [
        "is_critical",
        "category",
        "created_at",
        "feature__project",
        "tenant",
    ]
    search_fields = ["name", "description", "scenario"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "tenant",
                    "feature",
                    "category",
                    "name",
                    "description",
                )
            },
        ),
        (
            "ATAM Scenario (SEI Methodology)",
            {
                "fields": (
                    "scenario",
                    "stimulus",
                    "response",
                    "response_measure",
                    "environment",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Analysis",
            {
                "fields": (
                    "priority",
                    "is_critical",
                    "tradeoffs",
                )
            },
        ),
        (
            "Metadata",
            {"fields": ("created_by", "created_at", "updated_at")},
        ),
    )
    list_per_page = 25

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("feature", "feature__project", "category")
        )
