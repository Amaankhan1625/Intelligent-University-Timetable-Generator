# 📘 **University Timetable Generator (Django + Next.js + Genetic Algorithm)**

A full-stack automated timetable generator built using **Django REST Framework (backend)** and **Next.js (frontend)**. The system generates conflict-free timetables for multiple departments and sections using a **Genetic Algorithm** with real-time visualization, export options, and secure JWT authentication.

---

## 🚀 **1. Project Overview**

This project solves the highly complex and manual problem of university class scheduling. It automatically generates optimized, conflict-free timetables for:

* Multiple departments
* Multiple years
* Multiple sections
* Multiple instructors
* Theory, Lab, and Practical classes
* Custom meeting times
* Automatic lunch breaks

The Genetic Algorithm ensures:
✔ No instructor conflict
✔ No room conflict
✔ No student/section conflict
✔ Consecutive slots for labs
✔ Optimized distribution of classes
✔ High fitness score for best timetable

The frontend renders a **dynamic timetable grid** with draggable blocks (dragging shows a warning without modifying the timetable).

---

## 🛠 **2. Technologies Used**

### **Backend (Django + DRF)**

* Django
* Django REST Framework
* PostgreSQL (recommended)
* PyJWT
* Genetic Algorithm Engine
* ReportLab (PDF export)
* OpenPyXL (Excel export)

### **Frontend (Next.js + TypeScript)**

* Next.js 14
* React
* TailwindCSS
* HeroIcons
* Axios
* JWT Authentication
* React-Hot-Toast

---

## 🎯 **3. Core Features**

### **Backend Features**

✔ JWT Authentication
✔ CRUD for all scheduling entities:

* Departments
* Courses
* Sections
* Rooms
* Instructors
* Meeting Times
  ✔ Automatic meeting-time population (Mon–Fri, lunch included)
  ✔ Genetic Algorithm-based timetable generation
  ✔ Export timetable to **PDF** and **Excel**
  ✔ Timetable activation system (one active per department-year-semester)
  ✔ Conflict detection and fitness scoring

---

### **Frontend Features**

✔ Modern dashboard UI
✔ Timetable grid with drag warnings (no modifications allowed)
✔ Class color-coding based on type
✔ Dropdowns, modals, multi-selects
✔ Department/Year/Semester-based generation
✔ PDF & Excel export buttons
✔ View all previously generated timetables
✔ Fitness meter
✔ Course–Instructor mapping legend

---

## 🧬 **4. How Timetable Generation Works (Genetic Algorithm)**

1️⃣ Load all the **Sections**, **Courses**, **Instructors**, **Rooms**, and **Meeting Times**.
2️⃣ Build a list of “required classes” such as:

```
Section A → Course DBMS → 3 classes/week → Theory  
Section A → Course DS Lab → 1 class/week → 2-hour lab
```

3️⃣ Generate initial population:

* Random instructor assignment
* Random room assignment
* Valid time slot assignment (no lunch break)

4️⃣ Fitness scoring checks:

* Instructor conflict
* Room conflict
* Section conflict
* Time overlap
* Missing assignment penalty

5️⃣ GA operations:

* Tournament selection
* Single-point crossover
* Mutation (time/instructor/room change)
* Elite preservation

6️⃣ Best timetable saved to DB
7️⃣ Frontend visualizes schedule

---

## 🛢 **5. Database Structure (Simplified)**

```
Instructor
Room
MeetingTime
Department
Course
Section
Class
Timetable
```

Each `Timetable` stores many `Class` objects, each linked to:

* Course
* Instructor
* MeetingTime
* Room
* Section

---

## 📂 **6. Project Structure**

### **Backend (/scheduler_backend)**

```
scheduler_backend/
│── scheduler_app/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── genetic_algorithm.py
│   ├── utils.py
│   └── urls.py
│
├── manage.py
└── requirements.txt
```

### **Frontend (/frontend)**

```
frontend/
│── components/
│   └── TimetableGrid.tsx
│── app/
│   ├── dashboard/
│   │   ├── meeting-times/
│   │   ├── sections/
│   │   ├── timetables/
│   │   └── courses/
│── lib/api.ts
│── styles/globals.css
└── package.json
```

---

## ⚙️ **7. Installation Guide**

---

### **Backend Setup**

#### **1. Create Virtual Environment**

```
python -m venv env
source env/bin/activate   # macOS/Linux
env\Scripts\activate      # Windows
```

#### **2. Install Dependencies**

```
pip install -r requirements.txt
```

#### **3. Database Migration**

```
python manage.py makemigrations
python manage.py migrate
```

#### **4. Create Superuser**

```
python manage.py createsuperuser
```

#### **5. Run Server**

```
python manage.py runserver
```

---

### **Frontend Setup**

#### **1. Install Dependencies**

```
npm install
```

#### **2. Create `.env.local`**

```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api
```

#### **3. Run Frontend**

```
npm run dev
```

---

## 🔗 **8. API Overview (Important Endpoints)**

### **Authentication**

```
POST /auth/login/
GET  /auth/user/
POST /auth/change-password/
```

### **Meeting Times**

```
GET  /meeting-times/
POST /meeting-times/
POST /meeting-times/populate_default_slots/
```

### **Timetables**

```
POST /timetables/generate/
GET  /timetables/{id}/view_schedule/
GET  /timetables/{id}/export_pdf/
GET  /timetables/{id}/export_excel/
POST /timetables/{id}/activate/
```

---

## 🧩 **9. Export Features**

### PDF Export:

✔ Auto-layout timetable
✔ Course–Instructor mapping
✔ Academic metadata

### Excel Export:

✔ Each day as a column
✔ Time slots as rows
✔ Clean formatting

---

## 📦 **10. Deployment Notes**

### Backend:

* Use Gunicorn + Nginx
* Configure HTTPS
* Use PostgreSQL
* Enable CORS for frontend domain

### Frontend:

* Deploy using Vercel
* Update API URL in `.env.production`

---

## 🤝 **11. Contributing**

1. Fork the repository
2. Create a new feature branch
3. Commit changes
4. Open PR

---

## 📄 **12. License**

This project is licensed under the **MIT License**.

---

