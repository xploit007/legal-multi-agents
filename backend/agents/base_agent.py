"""
Base Agent class for all Legal Strategy Council agents.
"""
from abc import ABC, abstractmethod
from typing import Optional
import time
from groq import Groq
import config
import database


class BaseAgent(ABC):
    """Base class for all agents in the Legal Strategy Council."""

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.client = Groq(api_key=config.GROQ_API_KEY)

    def think(self, prompt: str, retry_count: int = 1) -> str:
        """
        Call Groq API with the given prompt.
        Includes retry logic for handling API errors.
        """
        print(f"[{self.name}] Calling Groq API with model: {config.GROQ_MODEL}")
        for attempt in range(retry_count + 1):
            try:
                print(f"[{self.name}] Attempt {attempt + 1}...")
                response = self.client.chat.completions.create(
                    model=config.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=config.GROQ_TEMPERATURE,
                    max_tokens=config.GROQ_MAX_TOKENS
                )
                print(f"[{self.name}] Groq API call successful")
                return response.choices[0].message.content
            except Exception as e:
                print(f"[{self.name}] Groq API error: {e}")
                if attempt < retry_count:
                    time.sleep(2)  # Wait before retry
                    continue
                raise Exception(f"Groq API error after {retry_count + 1} attempts: {str(e)}")

    def write_to_db(self, collection_name: str, document: dict) -> str:
        """
        Write a document to MongoDB.
        Returns the inserted document's ID.
        """
        collection = database.get_collection(collection_name)
        result = collection.insert_one(document)
        return str(result.inserted_id)

    def read_from_db(self, collection_name: str, query: dict) -> list:
        """
        Read documents from MongoDB.
        Returns a list of matching documents.
        """
        collection = database.get_collection(collection_name)
        documents = list(collection.find(query))
        # Remove MongoDB _id field for cleaner output
        for doc in documents:
            if "_id" in doc:
                del doc["_id"]
        return documents

    @abstractmethod
    def analyze(self, case_data: dict) -> dict:
        """
        Analyze the case and return results.
        Must be implemented by each specific agent.
        """
        pass
