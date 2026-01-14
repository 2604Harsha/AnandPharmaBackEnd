# 🏥 Anand Pharma – Backend API

Anand Pharma is a scalable backend system for an online pharmacy platform, built using FastAPI.
It supports authentication, product management, cart & checkout flow, prescription uploads,
order placement, billing, and online payments.

---

## 🚀 Tech Stack

- Backend Framework: FastAPI  
- Language: Python 3.11  
- Database: PostgreSQL (Async SQLAlchemy)  
- ORM: SQLAlchemy (Async)  
- Authentication: JWT (OAuth2)  
- Payments: Razorpay  
- Architecture: Modular API with RBAC  

---

## 📂 Project Structure

```
Anand Pharma/
├── app/
│   ├── api/routers/routes/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── uploads/
├── requirements.txt
└── README.md
```

---

## 🔑 Key Features

- JWT-based Authentication
- Role-Based Access Control (RBAC)
- Product & Stock Management
- Cart & Checkout Flow
- Prescription Upload & Medicine Matching
- Order Placement & Approval
- Razorpay Payment Integration
- Billing & Invoice Logic

---

## ⚙️ Setup Instructions

### Change Directory to app
```
cd app 
```

### 1. Create Virtual Environment
```
python -m venv venv
```

### 2. Activate Environment
```
venv\Scripts\activate
```

### 3. Install Dependencies
```
python -m pip install -r requirements.txt
pip install -r requirements.txt
```

### Database Reset (Creating all Tables & Reset Tables)
```
python reset_database.py
```

### Create a Admin Details
```
python create_admin.py

```
### 4.Seeding
```
python -m scripts.seed
python -m scripts.seed_products

```

### 5. Run Server
```
python -m uvicorn main:app --reload
```

Swagger Docs:
http://127.0.0.1:8000/docs

---

## 🔐 API Modules

| Module | Description |
|------|------------|
| Auth | User Authentication |
| Product | Product & Inventory |
| Cart | Cart Management |
| Checkout | Address & Checkout |
| Order | Order Placement |
| Payment | Razorpay Payments |
| Prescription | Prescription Upload |

---

## 🧠 Design Notes

- Fully asynchronous backend
- Clean modular structure
- Production-ready API design
- Easily extensible

---

## 👨‍💻 Developed By

Backend Developer Intern  
Anand Pharma Project
