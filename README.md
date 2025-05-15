# 📚 Django Library Management System
 
A web-based library system built using Django and PostgreSQL.  
Users can view available books, borrow them, and manage student/librarian accounts via a simple interface.
 
---
 
## 🚀 Features
 
- 📖 Add, edit, and delete books
- 👨‍🎓 Add and manage student records
- 🧑‍💼 Librarian/admin interface
- 📚 Book borrowing and return tracking
- ✅ ISBN validation from uploaded `.txt` file and during book creation
- 🗃️ PostgreSQL integration
- 📁 File upload support
- 🎨 Responsive HTML templates
- 🔐 Custom authentication via email/password (WIP or planned)
 
---
 
## 🗂️ Project Structure
 
```
library_site/
├── library_site/
├── main/
├── static/
├── media/    
├── templates/          
├── valid_isbns.txt     
├── manage.py
├── requirements.txt
├── .gitignore
```
 
---

## 💻 Requirements

- Python 3.10+
- Django 4.x
- PostgreSQL

---

## 📦 Installation

```bash
git clone https://github.com/YourUsername/library-management-system.git
cd library-management-system
python -m venv .venv
source .venv/bin/activate      # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

## ⚙️ Setup Database

1. Set your PostgreSQL config in `settings.py`
2. Run:

```bash
python manage.py makemigrations
python manage.py migrate
```

3. Create superuser:

```bash
python manage.py createsuperuser
```

---

## 🧪 Run the App

```bash
python manage.py runserver
```
 
Visit: http://127.0.0.1:8000/

---

## 🛠️ TODO / Future Plans

- ✅ Add full login/auth system
- ⏳ Improve admin UX
- ⏳ Add PDF export for borrowing logs
- ⏳ Connect to real ISBN database API

---
 
## 📜 License

This project is licensed under the MIT License.

---

## 🙋‍♂️ Author
 
Built by [@Nwankees](https://github.com/Nwankees) — Computer Science student at Kennesaw State University.
