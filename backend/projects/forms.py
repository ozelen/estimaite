from django import forms
from django.core.exceptions import ValidationError

from .models import Feature, Project


class ProjectForm(forms.ModelForm):
    """Form for creating and editing projects"""

    class Meta:
        model = Project
        fields = ["name", "slug", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Project name",
                }
            ),
            "slug": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "project-slug",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Project description",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # New project
            self.fields["slug"].required = False

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if not slug and self.cleaned_data.get("name"):
            from django.utils.text import slugify

            slug = slugify(self.cleaned_data["name"])

        # Check uniqueness within tenant
        if self.user and hasattr(self.user, "profile"):
            tenant = self.user.profile.tenant
            existing = Project.objects.filter(tenant=tenant, slug=slug)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError(f"A project with slug '{slug}' already exists.")

        return slug

    def save(self, commit=True):
        project = super().save(commit=False)
        if self.user and hasattr(self.user, "profile"):
            project.tenant = self.user.profile.tenant
            project.created_by = self.user

        if commit:
            project.save()
        return project


class FeatureForm(forms.ModelForm):
    """Form for creating and editing features"""

    class Meta:
        model = Feature
        fields = [
            "project",
            "parent",
            "feature_type",
            "title",
            "description",
            "priority",
            "status",
        ]
        widgets = {
            "project": forms.Select(attrs={"class": "form-control"}),
            "parent": forms.Select(attrs={"class": "form-control"}),
            "feature_type": forms.Select(attrs={"class": "form-control"}),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Feature title",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Feature description",
                }
            ),
            "priority": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0",
                }
            ),
            "status": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., open, in-progress, done",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        project_pk = kwargs.pop("project_pk", None)
        super().__init__(*args, **kwargs)

        # Filter projects and features by tenant
        if self.user and hasattr(self.user, "profile"):
            tenant = self.user.profile.tenant
            self.fields["project"].queryset = Project.objects.filter(
                tenant=tenant, is_active=True
            )
            self.fields["parent"].queryset = Feature.objects.filter(tenant=tenant)

            # Set default project if provided
            if project_pk:
                try:
                    project = Project.objects.get(pk=project_pk, tenant=tenant)
                    self.fields["project"].initial = project
                except Project.DoesNotExist:
                    pass

            # Filter parent options based on selected project
            if self.instance.pk:
                self.fields["parent"].queryset = self.fields["parent"].queryset.exclude(
                    pk=self.instance.pk
                )

    def save(self, commit=True):
        feature = super().save(commit=False)
        if self.user and hasattr(self.user, "profile"):
            feature.tenant = self.user.profile.tenant
            feature.created_by = self.user

        if commit:
            feature.save()
        return feature

