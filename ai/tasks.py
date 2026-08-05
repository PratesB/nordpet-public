from openai import OpenAI
from django.conf import settings
from clients.models import MedicalRecord
from django.shortcuts import get_object_or_404


def transcribe_recording(medical_record_id):
    try:
        medical_record = get_object_or_404(MedicalRecord, pk=medical_record_id)
        client_openai = OpenAI(api_key=settings.OPENAI_API_KEY)

        with open(medical_record.consultation_media.path, 'rb') as video_file:
            response = client_openai.audio.transcriptions.create(
                model="whisper-1",
                file=video_file,
                response_format="verbose_json",
                language="en",
            )
            
            medical_record.ai_transcription_consultation = response.text
            medical_record.save()
            return "Transcription completed successfully"
            
    except MedicalRecord.DoesNotExist:
        print("Medical Record not found")
        return "Medical Record not found"
    except Exception as e:
        print(f"Transcription Error: {e}")
        return f"Error: {e}" 



def generate_summary(id_medical_record: int):
    from .agents import SummaryAgent
    medical_record = get_object_or_404(MedicalRecord, pk=id_medical_record)
    
    if medical_record.ai_transcription_consultation:
        summary_agent = SummaryAgent()
        summary = summary_agent.run(medical_record.ai_transcription_consultation)
        medical_record.ai_summary_consultation = summary.summaries
        medical_record.save(update_fields=['ai_summary_consultation'])
        
    return 'Ok'