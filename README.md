# Multi-Tenant E-Commerce Platform

A production-ready multi-tenant e-commerce backend built with Django REST Framework where multiple vendors (tenants) can host their stores on a shared platform while maintaining complete data isolation.

## Features

- **Multi-Tenancy**: Shared database architecture with logical isolation per vendor
- **JWT Authentication**: Secure token-based auth with custom claims (tenant_id, role)
- **Role-Based Access Control**: Owner, Staff, and Customer roles with different permissions
- **RESTful APIs**: Complete CRUD operations for Products and Orders
- **Cloud-Ready**: Dockerfile configured for GCP Cloud Run deployment

## Tech Stack

- Python 3.10+
- Django 4.2
- Django REST Framework
- SimpleJWT for authentication
- SQLite (development) / PostgreSQL (production)
- Gunicorn + WhiteNoise (production)

---

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd AskmyIdentity
   ```

2. **Create virtual environment** (recommended)

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**

   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (for admin access)

   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server**

   ```bash
   python manage.py runserver
   ```

7. **Access the API**
   - API Root: http://127.0.0.1:8000/
   - Admin Panel: http://127.0.0.1:8000/admin/

---

## API Endpoints

### Authentication

| Method | Endpoint              | Description           | Auth Required |
| ------ | --------------------- | --------------------- | ------------- |
| POST   | `/api/token/`         | Obtain JWT token pair | No            |
| POST   | `/api/token/refresh/` | Refresh access token  | No            |
| POST   | `/api/register/`      | Register new user     | No            |

### Products

| Method | Endpoint              | Description                         | Roles        |
| ------ | --------------------- | ----------------------------------- | ------------ |
| GET    | `/api/products/`      | List all products (tenant-specific) | All          |
| POST   | `/api/products/`      | Create a product                    | Owner, Staff |
| GET    | `/api/products/{id}/` | Get product details                 | All          |
| PUT    | `/api/products/{id}/` | Update a product                    | Owner, Staff |
| DELETE | `/api/products/{id}/` | Delete a product                    | Owner, Staff |

### Orders

| Method | Endpoint            | Description                   | Roles        |
| ------ | ------------------- | ----------------------------- | ------------ |
| GET    | `/api/orders/`      | List orders (tenant-specific) | All          |
| POST   | `/api/orders/`      | Place a new order             | All          |
| GET    | `/api/orders/{id}/` | Get order details             | All          |
| PUT    | `/api/orders/{id}/` | Update order status           | Owner, Staff |
| DELETE | `/api/orders/{id}/` | Delete an order               | Owner, Staff |

### Tenants (Vendors)

| Method | Endpoint             | Description        | Roles |
| ------ | -------------------- | ------------------ | ----- |
| GET    | `/api/tenants/`      | Get tenant info    | Owner |
| PUT    | `/api/tenants/{id}/` | Update tenant info | Owner |

### Utility

| Method | Endpoint   | Description           |
| ------ | ---------- | --------------------- |
| GET    | `/`        | API documentation     |
| GET    | `/health/` | Health check endpoint |

---

## Multi-Tenancy Implementation

### Architecture: Shared Database with Logical Isolation

All tenants share the same database, but data is logically isolated using a `tenant` foreign key on all tenant-specific models.

### Key Components

#### 1. TenantAwareModel (Abstract Base Class)

```python
class TenantAwareModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        abstract = True
```

All tenant-specific models (Product, Order) inherit from this class, automatically adding the `tenant` field.

#### 2. TenantAwareViewSet (Query Filtering)

```python
class TenantAwareViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return self.queryset.filter(tenant=self.request.user.tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)
```

This ensures:

- Users can ONLY see data belonging to their tenant
- New records are automatically assigned to the user's tenant

#### 3. Custom JWT Claims

```python
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['tenant_id'] = user.tenant.id if user.tenant else None
        token['role'] = user.role
        return token
```

Every JWT access token includes `tenant_id` and `role` for authorization.

---

## Role-Based Access Control

### Roles

| Role         | Products  | Orders            | Users     |
| ------------ | --------- | ----------------- | --------- |
| **Owner**    | Full CRUD | Full CRUD         | Full CRUD |
| **Staff**    | Full CRUD | Full CRUD         | No Access |
| **Customer** | Read Only | Create + Read Own | No Access |

### Implementation

Custom permission classes in `core/permissions.py`:

- `TenantProductPermission`: Controls product access based on role
- `TenantOrderPermission`: Controls order access, customers can only see/create their own orders
- `TenantPermission`: Restricts tenant management to owners only

---

## Testing the API

### 1. Create a Tenant (via Admin)

Go to http://127.0.0.1:8000/admin/ and create a Tenant with name, subdomain, and owner_email.

### 2. Register a User

```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "vendor1", "email": "vendor1@example.com", "password": "securepass123", "role": "owner", "tenant_id": 1}'
```

### 3. Get JWT Token

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "vendor1", "password": "securepass123"}'
```

Response includes `access` and `refresh` tokens. Decode the access token at [jwt.io](https://jwt.io) to see `tenant_id` and `role` claims.

### 4. Create a Product

```bash
curl -X POST http://127.0.0.1:8000/api/products/ \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Product 1", "description": "Test product", "price": 29.99, "stock": 100}'
```

### 5. Place an Order

```bash
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"products": [1], "status": "pending"}'
```

---

## Deployment (GCP Cloud Run)

### Using Docker

```bash
# Build the image
docker build -t ecommerce-backend .

# Test locally
docker run -p 8000:8000 -e PORT=8000 ecommerce-backend
```

### Deploy to Cloud Run

```bash
# Authenticate with GCP
gcloud auth login

# Deploy
gcloud run deploy ecommerce-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DJANGO_SECRET_KEY=your-production-secret-key"
```

---

## Project Structure

```
AskmyIdentity/
├── ecommerce/              # Django project settings
│   ├── settings.py         # Configuration (DRF, JWT, CORS)
│   ├── urls.py             # Main URL routing
│   └── wsgi.py             # WSGI entry point
├── core/                   # Main application
│   ├── models.py           # Tenant, User, Product, Order
│   ├── serializers.py      # API serializers + CustomTokenObtainPairSerializer
│   ├── views.py            # TenantAwareViewSet + endpoints
│   ├── permissions.py      # Role-based permission classes
│   └── urls.py             # API routes
├── manage.py
├── requirements.txt
├── Dockerfile              # Cloud Run ready
└── README.md
```

---

## License

This project is submitted as part of an assignment.
