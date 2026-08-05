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



