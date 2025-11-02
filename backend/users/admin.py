from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Profile, Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "profile_count", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "slug", "is_active")
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    list_per_page = 25
    
    def profile_count(self, obj):
        """Display number of profiles in this tenant"""
        if obj.pk:
            return obj.profiles.count()
        return 0
    profile_count.short_description = "Users"
    
    def has_add_permission(self, request):
        """Allow superusers to always add tenants"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Allow superusers to always change tenants"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Allow superusers to always delete tenants"""
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        """Allow superusers to always view tenants"""
        return request.user.is_superuser
    
    def save_model(self, request, obj, form, change):
        """Save tenant - superadmins can always create tenants"""
        # Tenants are global entities, not tenant-scoped, so RLS allows all access
        # This method ensures the save works correctly
        super().save_model(request, obj, form, change)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"
    fields = ["tenant", "phone_number", "avatar", "bio"]


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "tenant", "phone_number", "created_at"]
    list_filter = ["tenant", "created_at"]
    search_fields = ["user__username", "user__email", "phone_number"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["user", "tenant"]
