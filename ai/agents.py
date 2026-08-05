from langchain_openai import ChatOpenAI
from django.conf import settings
from abc import abstractmethod, ABC
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal
import os



class BaseAgent(ABC):
    llm = ChatOpenAI(model_name='gpt-5-mini', api_key=settings.OPENAI_API_KEY)
    language: str = 'en'
    audience: str = 'veterinarian'


    @abstractmethod
    def _prompt(self, **kwargs): ...

    @abstractmethod
    def run(self): ...



class TriageResult(BaseModel):
    risk_level: Literal['green', 'yellow', 'orange', 'red'] = Field(description="The assigned risk level based on triage rules.")




class TriageAgent(BaseAgent):
    def _prompt(self):
        skill_path = os.path.join(settings.BASE_DIR, 'ai', 'skills', 'triage', 'SKILL.md')
        with open(skill_path, 'r', encoding='utf-8') as f:
            triage_prompt_text = f.read()
            
        prompt = ChatPromptTemplate.from_messages([
            ('system', triage_prompt_text),
            ('human', 'Species: {species}\nWeight: {weight}kg\nHeart Rate: {heart_rate} bpm\nRespiratory Rate: {respiratory_rate} rpm\nTemperature: {temperature}°C\nComplaint: {complaint}\nNotes: {notes}')
        ])
        return prompt
        
    def run(self, species, weight, heart_rate, respiratory_rate, temperature, complaint, notes):
        chain = self._prompt() | self.llm.with_structured_output(TriageResult)
        return chain.invoke({
            'species': species,
            'weight': weight,
            'heart_rate': heart_rate,
            'respiratory_rate': respiratory_rate,
            'temperature': temperature,
            'complaint': complaint,
            'notes': notes,
        })



class Summaries(BaseModel):
    summaries: str = Field(description="Summaries of the video transcription need to be in this format.")


class SummaryAgent(BaseAgent):
    def _prompt(self):
        skill_path = os.path.join(settings.BASE_DIR, 'ai', 'skills', 'summary', 'SKILL.md')
        with open(skill_path, 'r', encoding='utf-8') as f:
            summary_prompt_text = f.read()

        prompt = ChatPromptTemplate.from_messages([
            ('system', summary_prompt_text),
            ('human', 'language:{language} | audience:{audience}\nUse the transcript below:\n{transcript}')
        ])

        return prompt


    
    def run(self, transcription):
        chain = self._prompt() | self.llm.with_structured_output(Summaries)
        return chain.invoke({
            'language': self.language,
            'audience': self.audience,
            'transcript': transcription
        })



class ExamAnalyses(BaseModel):
    summary: str = Field(description="A concise clinical summary of the findings.")
    abnormal_parameters: list[str] = Field(description="List of abnormal parameters found in the exam. Format each as: Parameter | Value | Range | Classification")
    critical_warning: bool = Field(description="True if there are critical, life-threatening abnormalities that require immediate veterinary attention.")
    diagnostic_hypotheses: list[str] = Field(description="List of suspected conditions based on the findings.")


class ExamAnalysisAgent(BaseAgent):
    def _prompt(self):
        skill_path = os.path.join(settings.BASE_DIR, 'ai', 'skills', 'exam_analysis', 'SKILL.md')
        with open(skill_path, 'r', encoding='utf-8') as f:
            exam_analysis_prompt_text = f.read()

        prompt = ChatPromptTemplate.from_messages([
            ('system', exam_analysis_prompt_text),
            ('human', 'language: {language} | audience: {audience}\nExams: {exam_results}')])

        return prompt
    
    def run(self, exam_results):
        chain = self._prompt() | self.llm.with_structured_output(ExamAnalyses)
        return chain.invoke({
            'exam_results': exam_results, 
            'language': self.language, 
            'audience': self.audience
        })



class AssistantAgent(BaseAgent):
    def _prompt(self):
        from langchain_core.prompts import MessagesPlaceholder
        skill_path = os.path.join(settings.BASE_DIR, 'ai', 'skills', 'assistant', 'SKILL.md')
        with open(skill_path, 'r', encoding='utf-8') as f:
            assistant_prompt_text = f.read()

        prompt = ChatPromptTemplate.from_messages([
            ("system", assistant_prompt_text),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        return prompt
        
    def _get_context(self, animal_id, question):
        from langchain_community.vectorstores import LanceDB
        from langchain_openai import OpenAIEmbeddings
        import lancedb
        from clients.models import Animal
        
        try:
            pet = Animal.objects.get(id=animal_id)
            dob_str = pet.date_of_birth.strftime('%d/%m/%Y') if pet.date_of_birth else 'Unknown'
            created_at_str = pet.created_at.strftime('%d/%m/%Y %H:%M') if pet.created_at else 'Unknown'
            updated_at_str = pet.updated_at.strftime('%d/%m/%Y %H:%M') if pet.updated_at else 'Unknown'
            
            basic_info = (f"Patient Name: {pet.name}\nSpecies: {pet.get_specie_display()}\n"
                          f"Breed: {pet.breed}\nGender: {pet.get_gender_display()}\n"
                          f"Date of Birth: {dob_str}\nRegistration Date: {created_at_str}\n"
                          f"Last Updated: {updated_at_str}\nOwner: {pet.owner.name}")
        except Exception:
            basic_info = "Unknown Patient"
        
        db_path = os.path.join(settings.BASE_DIR, "lancedb_data")
        db = lancedb.connect(db_path)
        embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        
        try:
            vectorstore = LanceDB(connection=db, embedding=embeddings, table_name="animal_knowledge")
            retriever = vectorstore.as_retriever(search_kwargs={'k': 3, 'filter': f"metadata.animal_id = {animal_id}"})
            docs = retriever.invoke(question)
            context = "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"Error querying LanceDB for AssistantAgent: {e}")
            context = ""
            
        if not context.strip():
            context = "No previous medical records found for this patient in the system."
            
        return f"=== PATIENT BASIC INFO ===\n{basic_info}\n\n=== MEDICAL HISTORY ===\n{context}"

    def run(self, animal_id, question, chat_history):
        context = self._get_context(animal_id, question)
        
        chain = self._prompt() | self.llm
        result = chain.invoke({
            "context": context,
            "chat_history": chat_history,
            "question": question
        })
        return result.content
        
    def stream_run(self, animal_id, question, chat_history):
        context = self._get_context(animal_id, question)
        
        chain = self._prompt() | self.llm
        return chain.stream({
            "context": context,
            "chat_history": chat_history,
            "question": question
        })