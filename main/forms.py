from django import forms
from django.core.exceptions import ValidationError

from .models import Book, Borrow, Reservation, Student, Librarian

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'isbn', 'publisher',
            'year', 'language', 'quantity'
        ]
        widgets = {
            'language': forms.Select(choices=Book.LANGUAGE_CHOICES),
        }

class BorrowForm(forms.Form):
    reserve_if_unavailable = forms.BooleanField(
        required=False,
        label="Reserve this book if it's unavailable?"
    )

class ReturnForm(forms.Form):
    # Remove the student selection
    confirm = forms.BooleanField(label="Confirm return?", required=True)

    def __init__(self, *args, **kwargs):
        self.book = kwargs.pop('book', None)
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if not self.book or not self.student:
            raise ValidationError("Invalid book or student.")
        try:
            self.borrow_record = Borrow.objects.get(
                book=self.book,
                student=self.student,
                returned_at__isnull=True
            )
        except Borrow.DoesNotExist:
            raise ValidationError("You have no active borrow record for this book.")
        return cleaned_data

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'first_name', 'middle_initial', 'last_name',
            'sex', 'year', 'student_id'#, 'email'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_initial': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sex': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.Select(attrs={'class': 'form-select'}),
            'student_id': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable the student_id field
        self.fields['student_id'].disabled = True

class LibrarianProfileForm(forms.ModelForm):
    class Meta:
        model = Librarian
        fields = [
            'first_name', 'middle_initial', 'last_name',
            'sex', 'staff_id', 'email'
        ]
        widgets = {
            'sex': forms.Select(choices=Librarian.GENDER_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable the student_id field
        self.fields['staff_id'].disabled = True
        self.fields['email'].disabled = True

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['student']

class AddBookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'isbn', 'publisher',
            'year', 'language', 'quantity', 'cover'
        ]
        widgets = {
            'language': forms.Select(choices=Book.LANGUAGE_CHOICES),
        }


class RemoveBookForm(forms.Form):
    isbn = forms.CharField(
        max_length=17,
        label="ISBN of book to remove"
    )

    def clean_isbn(self):
        raw_isbn = self.cleaned_data['isbn']
        cleaned_isbn = raw_isbn.replace('-', '')
        return cleaned_isbn

class RegistrationForm(forms.Form):
    email = forms.EmailField(label="KSU Email")
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput
    )
    first_name = forms.CharField(max_length=30)
    middle_initial = forms.CharField(max_length=1, required=False)
    last_name = forms.CharField(max_length=30)
    sex = forms.ChoiceField(choices=Student.GENDER_CHOICES)
    identifier = forms.IntegerField(
        label="Student or Staff ID",
        help_text="Your numeric KSU ID"
    )
    year = forms.ChoiceField(
        choices=Student.YEAR_CHOICES,
        required=False,
        help_text="Only for students; leave blank if staff"
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match")
        return cleaned
