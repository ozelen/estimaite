from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify
from users.models import RLSModel, Tenant


class Project(RLSModel):
    """Project model - represents a software project or product"""

    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "projects_project"
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        unique_together = [["tenant", "slug"]]
        indexes = [
            models.Index(fields=["tenant", "slug"]),
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["created_by"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Feature(RLSModel):
    """Feature model - hierarchical feature tree with types (epic, story, task)"""

    FEATURE_TYPES = [
        ("epic", "Epic"),
        ("story", "Story"),
        ("task", "Task"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="features",
        db_index=True,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        db_index=True,
        help_text="Parent feature for hierarchical structure",
    )
    feature_type = models.CharField(
        max_length=10,
        choices=FEATURE_TYPES,
        default="story",
        db_index=True,
        help_text="Type of feature: Epic (large), Story (user story), Task (small work item)",
    )
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    priority = models.IntegerField(
        default=0,
        db_index=True,
        help_text="Priority level (higher = more important)",
    )
    status = models.CharField(
        max_length=50,
        default="open",
        db_index=True,
        help_text="Current status (e.g., open, in-progress, done)",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_features",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects_feature"
        verbose_name = "Feature"
        verbose_name_plural = "Features"
        indexes = [
            models.Index(fields=["project", "feature_type"]),
            models.Index(fields=["project", "status"]),
            models.Index(fields=["parent"]),
            models.Index(fields=["priority"]),
        ]
        ordering = ["-priority", "title"]

    def __str__(self):
        type_display = self.get_feature_type_display()
        return f"[{type_display}] {self.title}"

    def get_ancestors(self):
        """Get all ancestor features"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return reversed(ancestors)

    def get_descendants(self):
        """Get all descendant features"""
        return Feature.objects.filter(tenant=self.tenant, parent=self).select_related(
            "parent", "project"
        )


class Requirement(RLSModel):
    """Requirement model - requirements belonging to features"""

    REQUIREMENT_TYPES = [
        ("functional", "Functional"),
        ("non-functional", "Non-Functional"),
        ("constraint", "Constraint"),
        ("business", "Business Rule"),
    ]

    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name="requirements",
        db_index=True,
    )
    requirement_type = models.CharField(
        max_length=20,
        choices=REQUIREMENT_TYPES,
        default="functional",
        db_index=True,
    )
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    acceptance_criteria = models.TextField(
        blank=True,
        help_text="Acceptance criteria or conditions of satisfaction",
    )
    priority = models.IntegerField(
        default=0,
        db_index=True,
        help_text="Priority level (higher = more important)",
    )
    is_satisfied = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this requirement has been satisfied",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_requirements",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects_requirement"
        verbose_name = "Requirement"
        verbose_name_plural = "Requirements"
        indexes = [
            models.Index(fields=["feature", "requirement_type"]),
            models.Index(fields=["feature", "is_satisfied"]),
            models.Index(fields=["priority"]),
        ]
        ordering = ["-priority", "title"]

    def __str__(self):
        return f"{self.get_requirement_type_display()}: {self.title}"


class QualityAttributeCategory(RLSModel):
    """Hierarchical category model for quality attributes (SEI/ATAM framework)"""

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        db_index=True,
    )
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0, db_index=True)

    class Meta:
        db_table = "projects_qualityattributecategory"
        verbose_name = "Quality Attribute Category"
        verbose_name_plural = "Quality Attribute Categories"
        unique_together = [["tenant", "parent", "name"]]
        indexes = [
            models.Index(fields=["tenant", "order"]),
            models.Index(fields=["parent"]),
        ]
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def get_ancestors(self):
        """Get all ancestor categories"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return reversed(ancestors)


class QualityAttributeScenario(RLSModel):
    """Quality Attribute Scenario model following SEI/ATAM methodology"""

    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name="quality_attributes",
        db_index=True,
    )
    category = models.ForeignKey(
        QualityAttributeCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quality_attributes",
        db_index=True,
        help_text="Category for organizing quality attributes",
    )
    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Name of the quality attribute (e.g., Performance, Security)",
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the quality attribute",
    )
    # ATAM/SEI Scenario fields
    stimulus = models.TextField(
        blank=True,
        help_text="What triggers the concern for this quality attribute (ATAM: Stimulus)",
    )
    response = models.TextField(
        blank=True,
        help_text="How the system responds to the stimulus (ATAM: Response)",
    )
    response_measure = models.TextField(
        blank=True,
        help_text="How success is measured (ATAM: Response Measure)",
    )
    environment = models.TextField(
        blank=True,
        help_text="Context/environment where the stimulus occurs (ATAM: Environment)",
    )
    scenario = models.TextField(
        blank=True,
        help_text="Complete quality attribute scenario description",
    )
    priority = models.IntegerField(
        default=0,
        db_index=True,
        help_text="Priority level (higher = more important)",
    )
    is_critical = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this is a critical quality attribute",
    )
    tradeoffs = models.TextField(
        blank=True,
        help_text="Tradeoffs and architectural decisions related to this quality attribute",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_quality_attributes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects_qualityattributescenario"
        verbose_name = "Quality Attribute Scenario"
        verbose_name_plural = "Quality Attribute Scenarios"
        indexes = [
            models.Index(fields=["feature", "category"]),
            models.Index(fields=["feature", "is_critical"]),
            models.Index(fields=["priority"]),
        ]
        ordering = ["-priority", "-is_critical", "name"]

    def __str__(self):
        return f"{self.name} ({self.feature.title})"
