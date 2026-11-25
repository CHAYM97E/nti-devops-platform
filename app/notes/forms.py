from django import forms

from .models import Note


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "body", "attachment"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3})}
