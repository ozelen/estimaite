from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile, Tenant


class SignupForm(UserCreationForm):
    """Signup form that creates a user, tenant organization, and profile"""

    email = forms.EmailField(
        required=True, help_text="Required. Enter a valid email address."
    )

    # Tenant/Organization fields
    organization_name = forms.CharField(
        max_length=255,
        required=True,
        label="Organization Name",
        help_text="Name of your organization/company",
    )
    organization_slug = forms.SlugField(
        required=False,
        label="Organization URL Slug",
        help_text="Leave blank to auto-generate from organization name",
    )

    # Profile fields (optional)
    phone_number = forms.CharField(max_length=20, required=False, label="Phone Number")

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "organization_name",
            "organization_slug",
            "phone_number",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email required
        self.fields["email"].required = True

        # Style the fields
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Username"}
        )
        self.fields["email"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Email address"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Confirm password"}
        )
        self.fields["organization_name"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Your Organization Name"}
        )
        self.fields["organization_slug"].widget.attrs.update(
            {"class": "form-control", "placeholder": "org-slug (optional)"}
        )
        self.fields["phone_number"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Phone (optional)"}
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_organization_slug(self):
        slug = self.cleaned_data.get("organization_slug")
        organization_name = self.cleaned_data.get("organization_name")

        # Auto-generate slug if not provided
        if not slug and organization_name:
            from django.utils.text import slugify

            slug = slugify(organization_name)

        # Handle slug collisions by appending numbers (same logic as in save())
        if slug:
            base_slug = slug
            counter = 1
            while Tenant.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

        return slug

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()

            # Create tenant/organization
            # Slug is already validated and made unique in clean_organization_slug()
            organization_name = self.cleaned_data["organization_name"]
            organization_slug = self.cleaned_data["organization_slug"]

            tenant = Tenant.objects.create(
                name=organization_name, slug=organization_slug, is_active=True
            )

            # Create profile linking user to tenant
            Profile.objects.create(
                user=user,
                tenant=tenant,
                phone_number=self.cleaned_data.get("phone_number", ""),
            )

        return user
