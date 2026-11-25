from django.db import models


class Note(models.Model):
    """A short note stored in PostgreSQL (RDS in AWS)."""

    title = models.CharField(max_length=120)
    body = models.TextField(blank=True)
    # Optional upload: local disk in Compose, S3 when USE_S3_MEDIA=true.
    attachment = models.FileField(upload_to="attachments/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
