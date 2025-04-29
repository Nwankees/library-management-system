from django.contrib import admin
from .models import Student, Book, Borrow, Reservation, Librarian
# Register your models here.
admin.site.register(Student)
admin.site.register(Book)
admin.site.register(Borrow)
admin.site.register(Reservation)
admin.site.register(Librarian)