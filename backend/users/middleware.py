"""
Middleware to set tenant context for RLS (Row Level Security) in PostgreSQL.
This sets the current tenant_id in the PostgreSQL session variable that RLS policies use.
"""

from django.db import connection


class TenantContextMiddleware:
    """
    Middleware that sets the tenant_id in PostgreSQL session for RLS policies.

    The tenant_id is extracted from the user's profile and set using:
    SET LOCAL app.current_tenant_id = '<tenant_id>';

    This variable is then used by RLS policies to filter data.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set tenant context from user profile if authenticated
        try:
            if request.user.is_authenticated:
                try:
                    # Import here to avoid circular imports
                    from users.models import Profile

                    profile = request.user.profile
                    tenant_id = profile.tenant_id

                    with connection.cursor() as cursor:
                        # Set the tenant_id in PostgreSQL session variable
                        # This will be used by RLS policies
                        cursor.execute(
                            "SET LOCAL app.current_tenant_id = %s", [str(tenant_id)]
                        )
                except (AttributeError, Exception):
                    # User doesn't have a profile yet
                    # Don't set tenant context - RLS policies will handle NULL
                    pass
            else:
                # Anonymous users have no tenant context
                # Don't set tenant context - RLS policies will handle NULL
                pass
        except Exception:
            # If database connection fails, just continue
            # This allows the app to work even if DB is temporarily unavailable
            pass

        response = self.get_response(request)
        return response
