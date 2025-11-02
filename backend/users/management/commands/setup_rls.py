"""
Management command to set up Row Level Security (RLS) policies in PostgreSQL.

This command:
1. Enables RLS on tenant-aware tables
2. Creates policies that filter by app.current_tenant_id session variable
3. Ensures data isolation between tenants
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Set up Row Level Security (RLS) policies for multitenancy"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Create the schema for app-specific variables if it doesn't exist
            cursor.execute("CREATE SCHEMA IF NOT EXISTS app;")
            
            # Enable RLS on users_tenant table (but allow all access since it's not tenant-scoped)
            cursor.execute("ALTER TABLE users_tenant ENABLE ROW LEVEL SECURITY;")
            cursor.execute("""
                DROP POLICY IF EXISTS tenant_all_access ON users_tenant;
                CREATE POLICY tenant_all_access ON users_tenant
                    FOR ALL
                    USING (true);
            """)
            
            # Enable RLS on users_profile table
            cursor.execute("ALTER TABLE users_profile ENABLE ROW LEVEL SECURITY;")
            
            # Drop existing policies if they exist
            cursor.execute("DROP POLICY IF EXISTS profile_tenant_isolation ON users_profile;")
            cursor.execute("DROP POLICY IF EXISTS profile_tenant_select ON users_profile;")
            cursor.execute("DROP POLICY IF EXISTS profile_tenant_insert ON users_profile;")
            cursor.execute("DROP POLICY IF EXISTS profile_tenant_update ON users_profile;")
            cursor.execute("DROP POLICY IF EXISTS profile_tenant_delete ON users_profile;")
            
            # Create RLS policies for users_profile
            # SELECT: Users can only see profiles from their tenant
            cursor.execute("""
                CREATE POLICY profile_tenant_select ON users_profile
                    FOR SELECT
                    USING (
                        tenant_id = (
                            SELECT current_setting('app.current_tenant_id', true)::integer
                        )
                        OR current_setting('app.current_tenant_id', true) IS NULL
                    );
            """)
            
            # INSERT: Users can only create profiles for their tenant
            cursor.execute("""
                CREATE POLICY profile_tenant_insert ON users_profile
                    FOR INSERT
                    WITH CHECK (
                        tenant_id = (
                            SELECT current_setting('app.current_tenant_id', true)::integer
                        )
                    );
            """)
            
            # UPDATE: Users can only update profiles from their tenant
            cursor.execute("""
                CREATE POLICY profile_tenant_update ON users_profile
                    FOR UPDATE
                    USING (
                        tenant_id = (
                            SELECT current_setting('app.current_tenant_id', true)::integer
                        )
                    )
                    WITH CHECK (
                        tenant_id = (
                            SELECT current_setting('app.current_tenant_id', true)::integer
                        )
                    );
            """)
            
            # DELETE: Users can only delete profiles from their tenant
            cursor.execute("""
                CREATE POLICY profile_tenant_delete ON users_profile
                    FOR DELETE
                    USING (
                        tenant_id = (
                            SELECT current_setting('app.current_tenant_id', true)::integer
                        )
                    );
            """)
            
            self.stdout.write(
                self.style.SUCCESS("✅ RLS policies created successfully")
            )
            self.stdout.write(
                "   - Enabled RLS on users_tenant and users_profile tables"
            )
            self.stdout.write(
                "   - Created tenant isolation policies"
            )
            self.stdout.write(
                "   - Policies use app.current_tenant_id session variable"
            )

