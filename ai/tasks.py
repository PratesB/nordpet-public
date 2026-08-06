from openai import OpenAI
from django.conf import settings
from clients.models import MedicalRecord
from django.shortcuts import get_object_or_404
import os


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
    
    try:
        medical_record = get_object_or_404(MedicalRecord, pk=id_medical_record)
        
        if medical_record.ai_transcription_consultation:
            summary_agent = SummaryAgent()
            summary = summary_agent.run(medical_record.ai_transcription_consultation)
            medical_record.ai_summary_consultation = summary.summaries
            medical_record.save(update_fields=['ai_summary_consultation'])
            
        return 'Ok'
    except Exception as e:
        print(f"Summary Generation Error: {e}")
        return f"Error: {e}"



def ocr_and_markdown_file(medical_record_id):
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions


    try:
        medical_record = get_object_or_404(MedicalRecord, pk=medical_record_id)

        # Force onnxruntime here to prevent OCR crashes.Current RapidOCR models do not support torch natively.
        ocr_options = RapidOcrOptions(backend="onnxruntime")
        pipeline_options = PdfPipelineOptions(ocr_options=ocr_options)


        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        result = converter.convert(medical_record.exam_pdf.path)
        doc = result.document
        text = doc.export_to_markdown()

        medical_record.ai_exam_ocr_text = text
        medical_record.save()
        return "OCR and Markdown completed successfully"

    except MedicalRecord.DoesNotExist:
        print("Medical Record not found")
        return "Medical Record not found"
        
    except Exception as e:
        print(f"OCR and Markdown Error: {e}")
        return f"Error: {e}" 


def generate_exam_analysis(id_medical_record: int):
    from .agents import ExamAnalysisAgent
    
    try:
        medical_record = get_object_or_404(MedicalRecord, pk=id_medical_record)
        
        if medical_record.ai_exam_ocr_text:
            exam_analysis_agent = ExamAnalysisAgent()
            exam_analysis = exam_analysis_agent.run(medical_record.ai_exam_ocr_text)
            medical_record.ai_exam_interpretation = exam_analysis.model_dump() if hasattr(exam_analysis, 'model_dump') else exam_analysis.dict()
            medical_record.save(update_fields=['ai_exam_interpretation'])
            
        return 'Ok'
    except Exception as e:
        print(f"Exam Analysis Error: {e}")
        return f"Error: {e}"




def ingest_animal_knowledge(medical_record_id: int):
    from langchain_community.vectorstores import LanceDB
    from langchain_openai import OpenAIEmbeddings
    from langchain_core.documents import Document
    import lancedb
    
    try:
        medical_record = get_object_or_404(MedicalRecord, pk=medical_record_id)
        
        content = f"Date: {medical_record.created_at}\n"
        if medical_record.ai_summary_consultation:
            content += f"Consultation Summary: {medical_record.ai_summary_consultation}\n"
        if medical_record.ai_exam_interpretation:
            content += f"Exam Findings: {medical_record.ai_exam_interpretation}\n"
        if medical_record.clinical_note:
            content += f"Veterinarian Notes: {medical_record.clinical_note}\n"
            
        if medical_record.triage:
            content += f"Triage Info: Weight: {medical_record.triage.weight}kg, Temp: {medical_record.triage.temperature}C, Heart Rate: {medical_record.triage.heart_rate}, Respiratory Rate: {medical_record.triage.respiratory_rate}, Complaint: {medical_record.triage.complaint}, Notes: {medical_record.triage.notes}\n"
            
        doc = Document(
            page_content=content,
            metadata={"animal_id": medical_record.animal.id, "record_id": medical_record.id}
        )
        
        db_path = os.path.join(settings.BASE_DIR, "lancedb_data")
        db = lancedb.connect(db_path)
        embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        
        vectorstore = LanceDB(connection=db, embedding=embeddings, table_name="animal_knowledge")
        vectorstore.add_documents([doc])
        
        return "Knowledge ingested successfully"
    except Exception as e:
        print(f"Ingest Knowledge Error: {e}")
        return f"Error: {e}"