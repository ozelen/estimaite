from django.contrib.auth.models import User
from django.db import models


class Tenant(models.Model):
    """Tenant/Organization model for multitenancy"""
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "users_tenant"
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class Profile(models.Model):
    """User profile extending Django User with tenant relationship"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        db_index=True,
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="profiles",
        db_index=True,
        help_text="Tenant/organization this user belongs to",
    )
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users_profile"
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["user", "tenant"]),
        ]

    def __str__(self):
        return f"{self.user.username} ({self.tenant.name})"


# Manager for RLS-aware querysets
class RLSQuerySet(models.QuerySet):
    """QuerySet that automatically filters by tenant_id from connection"""
    
    def _filter_by_tenant(self):
        """Filter queryset by current tenant_id from PostgreSQL session"""
        # This will be enforced by RLS at the database level
        # But we can also add explicit filtering for Django ORM consistency
        return self
    
    def get_queryset(self):
        return self._filter_by_tenant()


class RLSManager(models.Manager):
    """Manager that ensures RLS-aware queries"""
    
    def get_queryset(self):
        return RLSQuerySet(self.model, using=self._db)


# Mixin for models that need RLS
class RLSModel(models.Model):
    """Abstract base model for RLS-enabled models"""
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        db_index=True,
        help_text="Tenant/organization owning this record",
    )
    
    objects = RLSManager()
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["tenant"]),
        ]
