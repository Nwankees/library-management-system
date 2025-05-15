import re, datetime
import isbnlib
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.utils import timezone

current_year = datetime.date.today().year

class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    YEAR_CHOICES = [
        ('FR', 'Freshman'),
        ('SO', 'Sophomore'),
        ('JR', 'Junior'),
        ('SR', 'Senior'),
    ]

    first_name      = models.CharField(max_length=30)
    middle_initial  = models.CharField(max_length=1, blank=True)
    last_name       = models.CharField(max_length=30)
    sex             = models.CharField(max_length=1, choices=GENDER_CHOICES)
    year            = models.CharField(
                        max_length=2,
                        choices=YEAR_CHOICES,
                        blank=True,
                        help_text="Class standing"
                     )
    student_id      = models.PositiveIntegerField(unique=True)
    email           = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.first_name} {self.middle_initial}. {self.last_name}"

class Book(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'), ('es', 'Spanish'), ('zh', 'Chinese'), ('hi', 'Hindi'),
        ('ar', 'Arabic'), ('bn', 'Bengali'), ('pt', 'Portuguese'), ('ru', 'Russian'),
        ('ja', 'Japanese'), ('de', 'German'), ('ko', 'Korean'), ('fr', 'French'),
        ('it', 'Italian'), ('tr', 'Turkish'), ('ta', 'Tamil'), ('vi', 'Vietnamese'),
        ('pl', 'Polish'), ('uk', 'Ukrainian'), ('ro', 'Romanian'), ('nl', 'Dutch'),
    ]

    title               = models.CharField(max_length=100)
    author              = models.CharField(max_length=200, blank=True)
    isbn                = models.CharField(max_length=17, unique=True)
    publisher           = models.CharField(max_length=100)
    year                = models.CharField(
                            max_length=4,
                            validators=[RegexValidator(r'^\d{4}$', 'Enter a 4-digit year')]
                         )
    language            = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    quantity            = models.PositiveIntegerField(default=1)

    # current borrow state
    is_borrowed         = models.BooleanField(default=False)
    borrowed_by         = models.ForeignKey(
                            Student, null=True, blank=True,
                            on_delete=models.SET_NULL,
                            related_name='current_books'
                         )
    borrowed_datetime   = models.DateTimeField(null=True, blank=True)
    to_be_returned      = models.DateTimeField(null=True, blank=True)
    returned_datetime   = models.DateTimeField(null=True, blank=True)

    cover = models.ImageField(
        upload_to='covers/', blank=True, null=True,
        help_text="Upload a cover image (optional)"
    )

    def __str__(self):
        return self.title

    def clean(self):
        # ISBN & metadata validation
        self.isbn = self.isbn.replace('-', '')
        if not isbnlib.is_isbn10(self.isbn) and not isbnlib.is_isbn13(self.isbn):
            raise ValidationError("Invalid ISBN")
        y = int(self.year)
        if y < 1300 or y > current_year:
            raise ValidationError("Year must be between 1300 and current year")
        try:
            meta = isbnlib.meta(self.isbn)
            if meta['Title'] != self.title:
                raise ValidationError("Title doesn’t match metadata")
            user_authors = re.split(r',\s*', self.author)
            if set(meta['Authors']) != set(user_authors):
                raise ValidationError("Authors don’t match metadata")
            if meta['Publisher'] != self.publisher:
                raise ValidationError("Publisher doesn’t match metadata")
            if str(meta.get('Year','')) != self.year:
                raise ValidationError("Year doesn’t match metadata")
            # note: isbnlib doesn’t provide language, skip that check or use Google API
        except Exception as e:
            raise ValidationError(f"Metadata check failed: {e}")

    def borrow(self, student: Student):
        #Check if student is already borrowing this book
        if Borrow.objects.filter(student=student, book=self, returned_at__isnull=True).exists():
            raise ValidationError("You already borrowed this book and haven't returned it.")

        #Proceed only if available
        if self.quantity > 0:
            now = datetime.datetime.now()
            self.quantity -= 1
            self.is_borrowed = True
            self.borrowed_by = student
            self.borrowed_datetime = now
            self.to_be_returned = now + datetime.timedelta(days=15)
            self.save()

            Borrow.objects.create(
                student=student,
                book=self,
                borrowed_at=self.borrowed_datetime,
                returned_due_date=self.to_be_returned
            )
        else:
            # quantity == 0:
            raise ValidationError("No copies available.")

    def return_book(self):
        now = datetime.datetime.now()
        self.returned_datetime = now
        self.quantity += 1
        self.is_borrowed = False
        self.save()


        next_person = self.reservation_set.order_by('reserved_at').first()
        if next_person:
            self.borrow(next_person.student)
            next_person.delete()


class Borrow(models.Model):
    student     = models.ForeignKey(Student, on_delete=models.CASCADE)
    book        = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrowed_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)
    returned_due_date =models.DateTimeField()

    class Meta:
        unique_together = ('student','book','borrowed_at')

    def calculate_late_fee(self):

        now = timezone.now()
        if self.returned_at:
            comparison_date = self.returned_at
        else:
            comparison_date = now

        days_late = (comparison_date.date() - self.returned_due_date.date()).days
        if days_late > 0:
            return days_late * 1000  # $1 per day
        return 0

class Reservation(models.Model):
    student   = models.ForeignKey(Student, on_delete=models.CASCADE)
    book      = models.ForeignKey(Book,    on_delete=models.CASCADE)
    reserved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'book')
        ordering = ['reserved_at']

class Librarian(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='librarian_profile',
    )
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    first_name     = models.CharField(max_length=30)
    middle_initial = models.CharField(max_length=1, blank=True)
    last_name      = models.CharField(max_length=30)
    sex            = models.CharField(max_length=1, choices=GENDER_CHOICES)
    staff_id       = models.PositiveIntegerField(unique=True)
    email          = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.first_name} {self.middle_initial}. {self.last_name}"

    def add_book(self, title, author, isbn, publisher, year, language):
        """Method to add books."""
        book = Book.objects.create(
            title=title,
            author=author,
            isbn=isbn,
            publisher=publisher,
            year=year,
            language=language
        )
        book.full_clean()
        book.save()

    def remove_book(self, isbn):
        """Method to remove books."""
        book = Book.objects.get(isbn=isbn)
        book.delete()

    def view_borrowed_books(self):
        """Method to view all borrowed books."""
        borrowed_books = Book.objects.filter(is_borrowed=True)
        return borrowed_books