"""
Management command to create a new tenant/organization.

Usage:
    python manage.py create_tenant "My Company" --slug my-company
    python manage.py create_tenant "Acme Corp"  # slug will be auto-generated
"""

from django.core.management.base import BaseCommand, CommandError
from users.models import Tenant


class Command(BaseCommand):
    help = "Create a new tenant/organization"

    def add_arguments(self, parser):
        parser.add_argument(
            "name",
            type=str,
            help="Name of the tenant/organization"
        )
        parser.add_argument(
            "--slug",
            type=str,
            help="URL-friendly slug (auto-generated from name if not provided)"
        )
        parser.add_argument(
            "--inactive",
            action="store_true",
            help="Create tenant as inactive",
        )

    def handle(self, *args, **options):
        name = options["name"]
        slug = options.get("slug")
        is_active = not options.get("inactive", False)
        
        # Generate slug from name if not provided
        if not slug:
            slug = Tenant._meta.get_field("slug").default if hasattr(Tenant._meta.get_field("slug"), "default") else None
            if not slug:
                from django.utils.text import slugify
                slug = slugify(name)
        
        # Check if slug already exists
        if Tenant.objects.filter(slug=slug).exists():
            raise CommandError(f"Tenant with slug '{slug}' already exists. Use --slug to specify a different slug.")
        
        # Create tenant
        tenant = Tenant.objects.create(
            name=name,
            slug=slug,
            is_active=is_active
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Successfully created tenant: {tenant.name} (slug: {tenant.slug})"
            )
        )
        self.stdout.write(f"   ID: {tenant.id}")
        self.stdout.write(f"   Active: {tenant.is_active}")
        
        return tenant

