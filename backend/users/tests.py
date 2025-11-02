from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.text import slugify

from .forms import SignupForm
from .models import Profile, Tenant


class TenantModelTest(TestCase):
    """Test cases for Tenant model"""

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Company", slug="test-company", is_active=True
        )

    def test_tenant_creation(self):
        """Test that tenant can be created"""
        self.assertEqual(self.tenant.name, "Test Company")
        self.assertEqual(self.tenant.slug, "test-company")
        self.assertTrue(self.tenant.is_active)
        self.assertIsNotNone(self.tenant.created_at)
        self.assertIsNotNone(self.tenant.updated_at)

    def test_tenant_str(self):
        """Test tenant string representation"""
        self.assertEqual(str(self.tenant), "Test Company")

    def test_tenant_slug_uniqueness(self):
        """Test that tenant slugs must be unique"""
        with self.assertRaises(Exception):
            Tenant.objects.create(name="Another Company", slug="test-company")

    def test_tenant_inactive(self):
        """Test creating an inactive tenant"""
        tenant = Tenant.objects.create(
            name="Inactive Company", slug="inactive-company", is_active=False
        )
        self.assertFalse(tenant.is_active)


class ProfileModelTest(TestCase):
    """Test cases for Profile model"""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Company", slug="test-company")
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.profile = Profile.objects.create(
            user=self.user, tenant=self.tenant, phone_number="1234567890"
        )

    def test_profile_creation(self):
        """Test that profile can be created"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.tenant, self.tenant)
        self.assertEqual(self.profile.phone_number, "1234567890")
        self.assertIsNotNone(self.profile.created_at)
        self.assertIsNotNone(self.profile.updated_at)

    def test_profile_str(self):
        """Test profile string representation"""
        self.assertEqual(
            str(self.profile), f"{self.user.username} ({self.tenant.name})"
        )

    def test_profile_one_to_one_user(self):
        """Test that profile has one-to-one relationship with user"""
        self.assertEqual(self.user.profile, self.profile)

    def test_profile_tenant_relationship(self):
        """Test that profile has foreign key to tenant"""
        self.assertIn(self.profile, self.tenant.profiles.all())

    def test_profile_optional_fields(self):
        """Test that profile optional fields work"""
        profile = Profile.objects.create(
            user=User.objects.create_user(
                username="user2", email="user2@example.com", password="pass123"
            ),
            tenant=self.tenant,
        )
        self.assertEqual(profile.phone_number, "")
        self.assertFalse(profile.avatar)  # ImageFieldFile evaluates to False when empty
        self.assertEqual(profile.bio, "")


class SignupFormTest(TestCase):
    """Test cases for SignupForm"""

    def test_form_valid_with_all_fields(self):
        """Test form validation with all fields provided"""
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
            "organization_name": "New Company",
            "organization_slug": "new-company",
            "phone_number": "1234567890",
        }
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_auto_generates_slug(self):
        """Test that slug is auto-generated if not provided"""
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
            "organization_name": "My Awesome Company",
            "phone_number": "",
        }
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())
        expected_slug = slugify("My Awesome Company")
        self.assertEqual(form.cleaned_data["organization_slug"], expected_slug)

    def test_form_duplicate_email(self):
        """Test that duplicate emails are rejected"""
        User.objects.create_user(
            username="existing", email="existing@example.com", password="pass123"
        )
        form_data = {
            "username": "newuser",
            "email": "existing@example.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
            "organization_name": "New Company",
        }
        form = SignupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_form_duplicate_slug(self):
        """Test that duplicate organization slugs are automatically made unique"""
        Tenant.objects.create(name="Existing", slug="existing-slug")
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
            "organization_name": "New Company",
            "organization_slug": "existing-slug",
        }
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())
        # Slug should be automatically adjusted to be unique
        self.assertEqual(form.cleaned_data["organization_slug"], "existing-slug-1")

    def test_form_save_creates_user_tenant_profile(self):
        """Test that saving form creates user, tenant, and profile"""
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
            "organization_name": "Test Company",
            "organization_slug": "test-company",
            "phone_number": "1234567890",
        }
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())

        user = form.save()

        # Check user was created
        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.email, "newuser@example.com")

        # Check tenant was created
        self.assertTrue(hasattr(user, "profile"))
        tenant = user.profile.tenant
        self.assertEqual(tenant.name, "Test Company")
        self.assertEqual(tenant.slug, "test-company")

        # Check profile was created
        self.assertEqual(user.profile.phone_number, "1234567890")

    def test_form_slug_collision_handling(self):
        """Test that form handles slug collisions by appending numbers"""
        Tenant.objects.create(name="Existing", slug="test-company")
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
            "organization_name": "Test Company",
        }
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())

        user = form.save()
        tenant = user.profile.tenant

        # Should auto-generate unique slug
        self.assertTrue(tenant.slug.startswith("test-company"))
        self.assertNotEqual(tenant.slug, "test-company")


class SignupViewTest(TestCase):
    """Test cases for signup_view"""

    def setUp(self):
        self.client = Client()
        self.signup_url = reverse("users:signup")

    def test_signup_get(self):
        """Test GET request to signup page"""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/signup.html")
        self.assertIsInstance(response.context["form"], SignupForm)

    def test_signup_post_valid(self):
        """Test POST request with valid data"""
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
            "organization_name": "Test Company",
            "organization_slug": "test-company",
        }
        response = self.client.post(self.signup_url, data=form_data)
        self.assertRedirects(response, reverse("users:profile"))

        # Check user was created and logged in
        self.assertTrue(User.objects.filter(username="newuser").exists())
        user = User.objects.get(username="newuser")
        self.assertTrue(hasattr(user, "profile"))

    def test_signup_post_invalid(self):
        """Test POST request with invalid data"""
        form_data = {
            "username": "newuser",
            "email": "invalid-email",
            "password1": "pass",
            "password2": "pass",
            "organization_name": "",
        }
        response = self.client.post(self.signup_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_signup_redirects_if_authenticated(self):
        """Test that authenticated users are redirected from signup"""
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        tenant = Tenant.objects.create(name="Test", slug="test")
        Profile.objects.create(user=user, tenant=tenant)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.signup_url)
        self.assertRedirects(response, reverse("users:profile"))


class LoginViewTest(TestCase):
    """Test cases for login_view"""

    def setUp(self):
        self.client = Client()
        self.login_url = reverse("users:login")
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.tenant = Tenant.objects.create(name="Test", slug="test")
        Profile.objects.create(user=self.user, tenant=self.tenant)

    def test_login_get(self):
        """Test GET request to login page"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")

    def test_login_post_valid(self):
        """Test POST request with valid credentials"""
        form_data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post(self.login_url, data=form_data)
        self.assertRedirects(response, reverse("users:profile"))

    def test_login_post_invalid(self):
        """Test POST request with invalid credentials"""
        form_data = {"username": "testuser", "password": "wrongpassword"}
        response = self.client.post(self.login_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_redirects_if_authenticated(self):
        """Test that authenticated users are redirected from login"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse("users:profile"))


class ProfileViewTest(TestCase):
    """Test cases for profile_view"""

    def setUp(self):
        self.client = Client()
        self.profile_url = reverse("users:profile")
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.tenant = Tenant.objects.create(name="Test Company", slug="test-company")
        self.profile = Profile.objects.create(
            user=self.user, tenant=self.tenant, phone_number="1234567890"
        )

    def test_profile_requires_login(self):
        """Test that profile view requires authentication"""
        response = self.client.get(self.profile_url)
        self.assertRedirects(
            response, f"{reverse('users:login')}?next={self.profile_url}"
        )

    def test_profile_view(self):
        """Test profile view for authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")
        self.assertEqual(response.context["profile"], self.profile)
        self.assertEqual(response.context["user"], self.user)
        self.assertEqual(response.context["tenant"], self.tenant)


class HomeViewTest(TestCase):
    """Test cases for home_view"""

    def setUp(self):
        self.client = Client()
        self.home_url = reverse("users:home")

    def test_home_view(self):
        """Test home page view"""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/home.html")

    def test_home_view_no_auth_required(self):
        """Test that home view doesn't require authentication"""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)


class IntegrationTest(TestCase):
    """Integration tests for signup flow"""

    def setUp(self):
        self.client = Client()

    def test_full_signup_flow(self):
        """Test complete signup flow"""
        signup_url = reverse("users:signup")
        profile_url = reverse("users:profile")

        # Step 1: Access signup page
        response = self.client.get(signup_url)
        self.assertEqual(response.status_code, 200)

        # Step 2: Submit signup form
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
            "organization_name": "New Company",
            "organization_slug": "new-company",
            "phone_number": "1234567890",
        }
        response = self.client.post(signup_url, data=form_data)
        self.assertRedirects(response, profile_url)

        # Step 3: Verify user can access profile
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("newuser", response.content.decode())

        # Step 4: Verify database state
        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(hasattr(user, "profile"))
        self.assertEqual(user.profile.tenant.name, "New Company")
        self.assertEqual(user.profile.phone_number, "1234567890")
