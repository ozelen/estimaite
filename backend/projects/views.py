from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import FeatureForm, ProjectForm
from .models import Feature, Project


@login_required
def project_list(request):
    """List all projects for the current user's tenant"""
    if not hasattr(request.user, "profile"):
        messages.error(request, "You need a profile to access projects.")
        return redirect("users:profile")

    tenant = request.user.profile.tenant
    projects = (
        Project.objects.filter(tenant=tenant)
        .annotate(feature_count=Count("features"))
        .order_by("-created_at")
    )

    return render(request, "projects/project_list.html", {"projects": projects})


@login_required
def project_detail(request, pk):
    """View project details with features"""
    if not hasattr(request.user, "profile"):
        messages.error(request, "You need a profile to access projects.")
        return redirect("users:profile")

    tenant = request.user.profile.tenant
    project = get_object_or_404(Project, pk=pk, tenant=tenant)

    # Get features grouped by type
    features = Feature.objects.filter(project=project, tenant=tenant).select_related(
        "parent", "created_by"
    )

    # Group by feature type
    features_by_type = {
        "epic": features.filter(feature_type="epic"),
        "story": features.filter(feature_type="story"),
        "task": features.filter(feature_type="task"),
    }

    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
            "features": features,
            "features_by_type": features_by_type,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def project_create(request):
    """Create a new project"""
    if not hasattr(request.user, "profile"):
        messages.error(request, "You need a profile to create projects.")
        return redirect("users:profile")

    if request.method == "POST":
        form = ProjectForm(request.POST, user=request.user)
        if form.is_valid():
            project = form.save()
            messages.success(request, f"Project '{project.name}' created successfully!")
            return redirect("projects:project_detail", pk=project.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProjectForm(user=request.user)

    return render(
        request, "projects/project_form.html", {"form": form, "action": "Create"}
    )


@login_required
@require_http_methods(["GET", "POST"])
def project_update(request, pk):
    """Update an existing project"""
    if not hasattr(request.user, "profile"):
        messages.error(request, "You need a profile to edit projects.")
        return redirect("users:profile")

    tenant = request.user.profile.tenant
    project = get_object_or_404(Project, pk=pk, tenant=tenant)

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project, user=request.user)
        if form.is_valid():
            project = form.save()
            messages.success(request, f"Project '{project.name}' updated successfully!")
            return redirect("projects:project_detail", pk=project.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProjectForm(instance=project, user=request.user)

    return render(
        request,
        "projects/project_form.html",
        {"form": form, "project": project, "action": "Edit"},
    )


@login_required
@require_http_methods(["GET", "POST"])
def project_delete(request, pk):
    """Delete a project"""
    if not hasattr(request.user, "profile"):
        messages.error(request, "You need a profile to delete projects.")
        return redirect("users:profile")

    tenant = request.user.profile.tenant
    project = get_object_or_404(Project, pk=pk, tenant=tenant)

    if request.method == "POST":
        project_name = project.name
        project.delete()
        messages.success(request, f"Project '{project_name}' deleted successfully!")
        return redirect("projects:project_list")

    return render(request, "projects/project_confirm_delete.html", {"project": project})


@login_required
def feature_list(request, project_pk=None):
    """List features, optionally filtered by project"""
    if not hasattr(request.user, "profile"):
        messages.error(request, "You need a profile to access features.")
        return redirect("users:profile")

    tenant = request.user.profile.tenant
    features = Feature.objects.filter(tenant=tenant).select_related("project", "parent")

    project = None
    if project_pk:
        project = get_object_or_404(Project, pk=project_pk, tenant=tenant)
        features = features.filter(project=project)

    # Group by feature type
    features_by_type = {
        "epic": features.filter(feature_type="epic"),
        "story": features.filter(feature_type="story"),
        "task": features.filter(feature_type="task"),
    }

    return render(
        request,
        "projects/feature_list.html",
        {
            "features": features,
            "project": project,
            "features_by_type": features_by_type,
        },
    )


@login_required
def feature_detail(request, pk):
    """View feature details"""
    if not hasattr(request.user, "profile"):
        messages.error(request, "You need a profile to access features.")
        return redirect("users:profile")

    tenant = request.user.profile.tenant
    feature = get_object_or_404(
        Feature.objects.select_related("project", "parent", "created_by"),
        pk=pk,
        tenant=tenant,
    )

    # Get requirements and quality attributes
    requirements = feature.requirements.all()
    quality_attributes = feature.quality_attributes.all().select_related("category")

    return render(
        request,
        "projects/feature_detail.html",
        {
            "feature": feature,
            "requirements": requirements,
            "quality_attributes": quality_attributes,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def feature_create(request, project_pk=None):
    """Create a new feature"""
    if not hasattr(request.user, "profile"):
        messages.error(request, "You need a profile to create features.")
        return redirect("users:profile")

    if request.method == "POST":
        form = FeatureForm(request.POST, user=request.user, project_pk=project_pk)
        if form.is_valid():
            feature = form.save()
            messages.success(
                request, f"Feature '{feature.title}' created successfully!"
            )
            return redirect("projects:feature_detail", pk=feature.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FeatureForm(user=request.user, project_pk=project_pk)

    # Get project if specified
    project = None
    if project_pk:
        tenant = request.user.profile.tenant
        project = get_object_or_404(Project, pk=project_pk, tenant=tenant)

    return render(
        request,
        "projects/feature_form.html",
        {"form": form, "action": "Create", "project": project},
    )


@login_required
@require_http_methods(["GET", "POST"])
def feature_update(request, pk):
    """Update an existing feature"""
    if not hasattr(request.user, "profile"):
        messages.error(request, "You need a profile to edit features.")
        return redirect("users:profile")

    tenant = request.user.profile.tenant
    feature = get_object_or_404(Feature, pk=pk, tenant=tenant)

    if request.method == "POST":
        form = FeatureForm(
            request.POST,
            instance=feature,
            user=request.user,
            project_pk=feature.project.pk,
        )
        if form.is_valid():
            feature = form.save()
            messages.success(
                request, f"Feature '{feature.title}' updated successfully!"
            )
            return redirect("projects:feature_detail", pk=feature.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FeatureForm(
            instance=feature, user=request.user, project_pk=feature.project.pk
        )

    return render(
        request,
        "projects/feature_form.html",
        {"form": form, "feature": feature, "action": "Edit"},
    )


@login_required
@require_http_methods(["GET", "POST"])
def feature_delete(request, pk):
    """Delete a feature"""
    if not hasattr(request.user, "profile"):
        messages.error(request, "You need a profile to delete features.")
        return redirect("users:profile")

    tenant = request.user.profile.tenant
    feature = get_object_or_404(Feature, pk=pk, tenant=tenant)

    if request.method == "POST":
        feature_title = feature.title
        project_pk = feature.project.pk
        feature.delete()
        messages.success(request, f"Feature '{feature_title}' deleted successfully!")
        return redirect("projects:project_detail", pk=project_pk)

    return render(request, "projects/feature_confirm_delete.html", {"feature": feature})
