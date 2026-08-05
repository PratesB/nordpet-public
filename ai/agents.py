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