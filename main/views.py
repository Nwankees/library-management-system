from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
# Make sure ValidationError is imported if you want to catch it
from django.core.exceptions import ValidationError
from django.urls import reverse

from .models import Book, Student, Borrow, Reservation, Librarian # Borrow might not be needed directly anymore
from .forms import BookForm, BorrowForm, ReturnForm, StudentProfileForm, LibrarianProfileForm, AddBookForm, RemoveBookForm, RegistrationForm # BorrowForm might still be needed for student selection,
import datetime
from django.utils import timezone
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required, user_passes_test

User = get_user_model()

def is_student(user):
    return user.groups.filter(name='Student').exists()

def is_librarian(user):
    return user.groups.filter(name='Librarian').exists()
# Create your views here.
def index(request):
    return render(request, "index.html")
def view_books(request):
    book_obj = Book.objects.all()
    context = {
        'books' : book_obj
    }
    return render(request, "books.html", context)

@login_required
@user_passes_test(is_librarian)
def view_students(request):
    student_obj = Student.objects.all()
    context = {
        'students' : student_obj
    }
    return render(request, "students.html", context)

#@login_required
def view_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    borrow_records = Borrow.objects.filter(book=book)
    is_lib = request.user.is_authenticated and is_librarian(request.user)

    already_reserved = False
    already_borrowed = False

    if request.user.is_authenticated and request.user.groups.filter(name='Student').exists():
        student = request.user.student_profile
        already_reserved = Reservation.objects.filter(student=student, book=book).exists()
        already_borrowed = Borrow.objects.filter(
            student=student,
            book=book,
            returned_at__isnull=True
        ).exists()

    context = {
        'book': book,
        'borrow_records': borrow_records,
        'is_librarian': is_lib,
        'already_reserved': already_reserved,
        'already_borrowed': already_borrowed,
    }

    return render(request, "book.html", context)


@login_required
@user_passes_test(is_librarian)
def new_book(request):
    if request.method == 'POST':
        form = AddBookForm(request.POST, request.FILES)  # ✅ Correct form + include FILES
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Book added successfully.")
                return redirect('books')
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
            messages.error(request, "Form is invalid. Check for errors below.")
    else:
        form = AddBookForm()

    return render(request, 'new_book.html', {'form': form})


@login_required
@user_passes_test(is_student)
def borrow(request, book_id):
    book    = get_object_or_404(Book, id=book_id)
    student = request.user.student_profile

    if request.method == 'POST':
        form = BorrowForm(request.POST)
        if form.is_valid():
            want_reserve = form.cleaned_data['reserve_if_unavailable']

            if book.quantity > 0:
                try:
                    book.borrow(student=student)
                    messages.success(request, "You have successfully borrowed this book.")
                except ValidationError as e:
                    messages.error(request, f"Error: {e.message if hasattr(e,'message') else e}")
            else:
                if want_reserve:
                    Reservation.objects.get_or_create(
                        student=student,
                        book=book,
                        defaults={'reserved_at': timezone.now()}
                    )
                    messages.success(request, "No copies available—YOU have been added to the reservation queue.")
                else:
                    messages.error(request, "Book cannot be borrowed right now.")
        else:
            messages.error(request, "Please correct the errors below.")

        # ✅ Redirect back to the same book page
        return redirect('book', book_id=book.id)

    else:
        form = BorrowForm(initial={'student': student})

    # if GET request, show the borrow page normally
    return render(request, 'borrow.html', {
        'form':    form,
        'book':    book,
        'student': student,
    })

@login_required
@user_passes_test(is_student)
def return_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    student = request.user.student_profile

    if request.method == 'POST':
        form = ReturnForm(request.POST, book=book, student=student)
        if form.is_valid():
            borrow = form.borrow_record
            borrow.returned_at = timezone.now()
            borrow.save()
            book.return_book()
            messages.success(request, f"Book '{book.title}' returned successfully.")
            return redirect('books')
    else:
        form = ReturnForm(book=book, student=student)

    return render(request, 'return.html', {'form': form, 'book': book})

@login_required
@user_passes_test(is_student)
def change_student_profile(request):
    student = request.user.student_profile
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            #   This will help fix the base.html ot changing the name
            user = request.user
            user.first_name = student.first_name
            user.last_name = student.last_name
            user.save()

            messages.success(request, "Student profile updated.")
            return redirect('student_profile_change')
    else:
        form = StudentProfileForm(instance=student)

    return render(request, 'student_profile_change.html', {
        'form': form,
        'student': student,
    })

@login_required
@user_passes_test(is_librarian)
def change_librarian_profile(request):
    librarian = request.user.librarian_profile
    if request.method == 'POST':
        form = LibrarianProfileForm(request.POST, instance=librarian)
        if form.is_valid():
            form.save()

            user = request.user
            user.first_name = librarian.first_name
            user.last_name = librarian.last_name
            user.save()

            messages.success(request, "Librarian profile updated.")
            return redirect('librarian_profile_change')
    else:
        form = LibrarianProfileForm(instance=librarian)

    return render(request, 'librarian_profile_change.html', {
        'form': form,
        'librarian': librarian,
    })

@login_required
@user_passes_test(is_librarian)
def librarian_borrowed_books(request):
    librarian = request.user.librarian_profile
    # your model method returns all Book.objects.filter(is_borrowed=True)
    borrowed_books = librarian.view_borrowed_books()              # :contentReference[oaicite:0]{index=0}&#8203;:contentReference[oaicite:1]{index=1}
    return render(request, 'librarian/borrowed_books.html', {
        'librarian': librarian,
        'borrowed_books': borrowed_books,
    })

@login_required
@user_passes_test(is_librarian)
def librarian_add_book(request):
    librarian = request.user.librarian_profile
    if request.method == 'POST':
        form = AddBookForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            librarian.add_book(                                       # :contentReference[oaicite:2]{index=2}&#8203;:contentReference[oaicite:3]{index=3}
                title=cd['title'],
                author=cd['author'],
                isbn=cd['isbn'],
                publisher=cd['publisher'],
                year=cd['year'],
                language=cd['language']
            )
            messages.success(request, "Book added to inventory.")
            return redirect('librarian_borrowed_books')
    else:
        form = AddBookForm()
    return render(request, 'librarian/add_book.html', {
        'form': form,
        'librarian': librarian,
    })

@login_required
@user_passes_test(is_librarian)
def librarian_remove_book(request):
    librarian = request.user.librarian_profile
    if request.method == 'POST':
        form = RemoveBookForm(request.POST)
        if form.is_valid():
            isbn = form.cleaned_data['isbn']
            try:
                librarian.remove_book(isbn)                           # :contentReference[oaicite:4]{index=4}&#8203;:contentReference[oaicite:5]{index=5}
                messages.success(request, "Book removed from inventory.")
            except Book.DoesNotExist:
                messages.error(request, "No book found with that ISBN.")
            return redirect('librarian_borrowed_books')
    else:
        form = RemoveBookForm()
    return render(request, 'librarian/remove_book.html', {
        'form': form,
        'librarian': librarian,
    })

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    student = request.user.student_profile
    borrowed_books = Borrow.objects.filter(student=student).order_by('-borrowed_at')

    context = {
        'borrowed_books': borrowed_books,
        'student': student,
    }
    return render(request, 'student_dashboard.html', context)

@login_required
@user_passes_test(is_librarian)
def librarian_dashboard(request):
    return render(request, 'librarian_dashboard.html')


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # After successfully creating the user:

            email    = form.cleaned_data['email']
            pwd      = form.cleaned_data['password1']
            first    = form.cleaned_data['first_name']
            middle   = form.cleaned_data['middle_initial']
            last     = form.cleaned_data['last_name']
            sex      = form.cleaned_data['sex']
            ident    = form.cleaned_data['identifier']
            year     = form.cleaned_data['year']
            domain   = email.split('@')[-1].lower()

            # Create the Django User
            user = User.objects.create_user(
                username=email,
                email=email,
                password=pwd,
                first_name=first,
                last_name=last
            )

            # Assign to group & create profile
            if domain == 'students.kennesaw.edu':
                grp, _ = Group.objects.get_or_create(name='Student')
                user.groups.add(grp)
                Student.objects.create(
                    user=user,
                    first_name=first,
                    middle_initial=middle,
                    last_name=last,
                    sex=sex,
                    year=year,
                    student_id=ident,
                    email=email
                )
                messages.success(request, "Registered as Student. Please log in.")
            elif domain == 'staff.kennesaw.edu':
                grp, _ = Group.objects.get_or_create(name='Librarian')
                user.groups.add(grp)
                Librarian.objects.create(
                    user=user,
                    first_name=first,
                    middle_initial=middle,
                    last_name=last,
                    sex=sex,
                    staff_id=ident,
                    email=email
                )
                messages.success(request, "Registered as Librarian. Please log in.")
            else:
                user.delete()
                form.add_error('email',
                    "Use your @students.kennesaw.edu or @staff.kennesaw.edu address.")
                return render(request, 'register.html', {'form': form})
            login(request, user)  # Log the user in immediately
            messages.success(request, "Account created and you are now logged in!")

            return redirect('books')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'login.html'    # our custom template

    def get_success_url(self):
        user = self.request.user
        if user.groups.filter(name='Student').exists():
            return reverse('student_dashboard')  # Change to your student dashboard URL
        elif user.groups.filter(name='Librarian').exists():
            return reverse('librarian_dashboard')  # Librarian's default dashboard
        else:
            return '/'  # fallback to home

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('student_dashboard' if is_student(request.user) else 'librarian_dashboard')
        return super().dispatch(request, *args, **kwargs)