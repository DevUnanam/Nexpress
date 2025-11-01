# FedEx Clone - Django Project Setup

## Project Overview
A Django-based shipping and delivery management system with role-based user authentication and Tailwind CSS styling.

## Quick Start

### 1. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 3. Run Development Server
```bash
python manage.py runserver
```

### 4. Build Tailwind CSS (Optional - CDN is already configured)
```bash
npm run build:css
```

## Project Structure

```
fedex_clone/
├── core/                          # Main application
│   ├── templates/core/
│   │   ├── home.html             # Home page
│   │   ├── login.html            # Login page
│   │   └── register.html         # Registration page
│   ├── admin.py                  # Admin configuration
│   ├── forms.py                  # UserRegistrationForm
│   ├── models.py                 # UserProfile model
│   ├── urls.py                   # App URLs
│   └── views.py                  # Views (HomeView, RegisterView)
├── fedex_clone/                   # Project configuration
│   ├── settings.py               # Django settings
│   └── urls.py                   # Main URL configuration
├── templates/
│   └── base.html                 # Base template with navbar
├── static/
│   ├── css/
│   │   ├── input.css             # Tailwind input
│   │   └── output.css            # Tailwind output
│   └── js/
├── tailwind.config.js            # Tailwind configuration
└── package.json                  # NPM dependencies
```

## Key Features

### 1. Custom User Model (UserProfile)
Located in `core/models.py`:
- Extends Django's AbstractUser
- Role-based authentication with choices:
  - Admin
  - Shipper
  - Courier
  - Recipient
- Additional fields: phone_number, address

### 2. Registration System
- **Form**: `core/forms.py` - UserRegistrationForm with Tailwind classes
- **View**: `core/views.py` - RegisterView (Class-based view)
- **Template**: `core/templates/core/register.html`
- **URL**: `/register/`

### 3. Tailwind CSS Configuration
Custom royal blue theme configured in `tailwind.config.js`:
```javascript
colors: {
  primary: {
    DEFAULT: '#0B5FFF',
    600: '#0A4EF2',
    // ... more shades
  }
}
```

## Essential Settings Changes

### INSTALLED_APPS (in fedex_clone/settings.py)
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',  # Added
]
```

### STATICFILES Configuration
```python
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### TEMPLATES Configuration
```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Added
        'APP_DIRS': True,
        # ...
    },
]
```

### Custom User Model
```python
AUTH_USER_MODEL = 'core.UserProfile'

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'login'
```

## URLs Configuration

### Main URLs (fedex_clone/urls.py)
```python
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
```

### App URLs (core/urls.py)
```python
from django.urls import path
from .views import HomeView, RegisterView

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('register/', RegisterView.as_view(), name='register'),
]
```

## Available Pages

1. **Home**: http://localhost:8000/
2. **Register**: http://localhost:8000/register/
3. **Login**: http://localhost:8000/login/
4. **Admin**: http://localhost:8000/admin/

## User Roles

- **Admin**: System management and oversight
- **Shipper**: Send packages
- **Courier**: Deliver packages
- **Recipient**: Receive packages

## Next Steps

1. Run migrations to create database tables
2. Create a superuser to access the admin panel
3. Start the development server
4. Navigate to the registration page to create users with different roles
5. Test the authentication flow

## Notes

- Tailwind CSS is configured to use CDN for quick setup
- To use the compiled version, run `npm run build:css` and update base.html
- The navbar shows different options based on authentication status
- User roles are displayed in the navbar when logged in
