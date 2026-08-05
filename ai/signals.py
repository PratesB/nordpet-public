from django.db.models.signals import post_save
from django.dispatch import receiver
from clients.models import MedicalRecord
from django_q.tasks import async_task



@receiver(post_save, sender=MedicalRecord)
def transcription_recording_ocr(sender, instance, created, **kwargs):
    if instance.consultation_media and not instance.ai_transcription_consultation:
        async_task('ai.tasks.transcribe_recording', instance.id)
    
    if instance.ai_transcription_consultation and not instance.ai_summary_consultation:
        async_task('ai.tasks.generate_summary', instance.id)
