import isbnlib, os
from django.core.management.base import BaseCommand
from main.models import Book

class Command(BaseCommand):
    help = "Import books from a newline-delimited ISBN file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file", "-f",
            default="valid_isbns.txt",
            help="Path to ISBN list (one per line)"
        )
        parser.add_argument(
            "--qty", "-q",
            type=int, default=5,
            help="Default quantity for each book"
        )

    def handle(self, *args, **options):
        path = options["file"]
        if not os.path.exists(path):
            return self.stderr.write(self.style.ERROR(f"File not found: {path}"))

        with open(path) as f:
            isbns = [l.strip() for l in f if l.strip()]

        for isbn in isbns:
            try:
                meta = isbnlib.meta(isbn)
                if not meta:
                    self.stdout.write(self.style.WARNING(f"No metadata: {isbn}"))
                    continue

                obj, created = Book.objects.get_or_create(
                    isbn=isbn,
                    defaults={
                        "title":     meta.get("Title", ""),
                        "author":    ", ".join(meta.get("Authors", [])),
                        "publisher": meta.get("Publisher", ""),
                        "year":      meta.get("Year", ""),
                        "language":  meta.get("Language", "en").lower(),
                        "quantity":  options["qty"],
                    }
                )
                msg = "Added" if created else "Skipped"
                self.stdout.write(f"{msg}: {obj.title} ({isbn})")

            except Exception as e:
                self.stderr.write(f"Error {isbn}: {e}")
