"""
URL configuration for library_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from main.views import (
    view_books, view_students, view_book, new_book, index,
    borrow, return_book, change_student_profile, change_librarian_profile,
    librarian_borrowed_books, librarian_add_book, librarian_remove_book,
    register, CustomLoginView, librarian_dashboard, student_dashboard
)
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    # Register and Login
    path('register/', register, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Password-change (must be logged in)
    path(
      'password_change/',
      auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change_form.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),

    # Public pages
    path('', index, name='index'),
    path('admin/', admin.site.urls),
    path('books/', view_books, name='books'),
    path('book/<int:book_id>/', view_book, name='book'),

    # Student actions
    path('new_book/', new_book, name='new_book'),        # Only librarians can add new books
    path('borrow/<int:book_id>/', borrow, name='borrow'),
    path('return/<int:book_id>/', return_book, name='return'),
    path('student/profile/change/', change_student_profile, name='student_profile_change'),
    path('student/dashboard/', student_dashboard, name='student_dashboard'),

    # Librarian actions
    path('students/', view_students, name='view_students'),
    path('librarian/borrowed/', librarian_borrowed_books, name='librarian_borrowed_books'),
    path('librarian/add_book/', librarian_add_book, name='librarian_add_book'),
    path('librarian/remove_book/', librarian_remove_book, name='librarian_remove_book'),
    path('librarian/profile/change/', change_librarian_profile, name='librarian_profile_change'),
    path('librarian/dashboard/', librarian_dashboard, name='librarian_dashboard'),
]

#The media fix
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)