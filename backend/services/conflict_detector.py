"""
Conflict Detector Service - Identifies disagreements between agents.
This is NOT an LLM agent, but a service that uses LLM for analysis.
"""
import json
import time
from typing import List, Dict
from groq import Groq
import config
import database
from models.schemas import Conflict


CONFLICT_DETECTION_PROMPT = """Compare these legal arguments and identify any contradictions, disagreements, or tensions between them.

For each conflict found, provide:
- agents_involved: list of agent names that disagree
- issue: brief title of the conflict (5-10 words)
- description: detailed explanation of the disagreement

Return your response as a JSON array of conflicts. If no conflicts are found, return an empty array [].

Example format:
[
  {
    "agents_involved": ["Lead Strategist", "Precedent Expert"],
    "issue": "Settlement vs Trial approach",
    "description": "The Lead Strategist recommends aggressive litigation while the Precedent Expert suggests precedents favor settlement."
  }
]

IMPORTANT: Return ONLY valid JSON, no other text."""


class ConflictDetector:
    """Service that detects conflicts between agent arguments."""

    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)

    def detect_conflicts(self, case_id: str) -> List[Dict]:
        """
        Read all arguments from MongoDB, analyze for conflicts,
        write conflicts to MongoDB, and return the list.
        """
        print(f"[ConflictDetector] Starting conflict analysis for case: {case_id}")

        # Read all arguments
        arguments_collection = database.get_arguments_collection()
        arguments = list(arguments_collection.find({"case_id": case_id}))
        print(f"[ConflictDetector] Found {len(arguments)} arguments")

        # Read all counterarguments
        counterarguments_collection = database.get_counterarguments_collection()
        counterarguments = list(counterarguments_collection.find({"case_id": case_id}))

        if not arguments and not counterarguments:
            return []

        # Format arguments for analysis
        arguments_text = self._format_arguments(arguments, counterarguments)

        # Call Groq to analyze conflicts
        conflicts_data = self._analyze_conflicts(arguments_text)

        # Save conflicts to MongoDB and return
        saved_conflicts = self._save_conflicts(case_id, conflicts_data)

        return saved_conflicts

    def _format_arguments(self, arguments: list, counterarguments: list) -> str:
        """Format all arguments for the LLM prompt."""
        text = "ARGUMENTS FROM LEGAL TEAM:\n\n"

        for arg in arguments:
            agent = arg.get('agent', 'Unknown Agent')
            arg_type = arg.get('type', 'unknown')
            content = arg.get('content', 'No content')
            text += f"=== {agent} ({arg_type}) ===\n{content}\n\n"

        if counterarguments:
            text += "\nCOUNTERARGUMENTS (ADVERSARIAL ANALYSIS):\n\n"
            for counter in counterarguments:
                agent = counter.get('agent', 'Unknown Agent')
                content = counter.get('content', 'No content')
                text += f"=== {agent} ===\n{content}\n\n"

        return text

    def _analyze_conflicts(self, arguments_text: str, retry_count: int = 1) -> List[Dict]:
        """Call Groq to analyze arguments for conflicts."""
        prompt = f"{CONFLICT_DETECTION_PROMPT}\n\n{arguments_text}"

        for attempt in range(retry_count + 1):
            try:
                response = self.client.chat.completions.create(
                    model=config.GROQ_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a legal analyst that identifies conflicts and disagreements between legal arguments. Always respond with valid JSON."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,  # Lower temperature for more consistent JSON
                    max_tokens=1500
                )

                response_text = response.choices[0].message.content.strip()

                # Try to parse JSON from response
                conflicts = self._parse_json_response(response_text)
                return conflicts

            except Exception as e:
                if attempt < retry_count:
                    time.sleep(2)
                    continue
                print(f"Error analyzing conflicts: {str(e)}")
                return []

    def _parse_json_response(self, response_text: str) -> List[Dict]:
        """Parse JSON from LLM response, handling various formats."""
        # Try direct parsing first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON array in response
        try:
            # Look for array brackets
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            if start != -1 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in code blocks
        try:
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass

        # Return empty if parsing fails
        print(f"Could not parse conflicts JSON from response")
        return []

    def _save_conflicts(self, case_id: str, conflicts_data: List[Dict]) -> List[Dict]:
        """Save conflicts to MongoDB and return saved documents."""
        if not conflicts_data:
            return []

        conflicts_collection = database.get_conflicts_collection()
        saved_conflicts = []

        for conflict_data in conflicts_data:
            # Validate conflict data
            agents_involved = conflict_data.get('agents_involved', [])
            issue = conflict_data.get('issue', 'Unknown conflict')
            description = conflict_data.get('description', 'No description provided')

            # Ensure agents_involved is a list
            if isinstance(agents_involved, str):
                agents_involved = [agents_involved]

            # Create conflict document
            conflict = Conflict(
                case_id=case_id,
                agents_involved=agents_involved,
                issue=issue,
                description=description,
                status="unresolved"
            )

            # Save to MongoDB
            conflict_dict = conflict.to_dict()
            conflicts_collection.insert_one(conflict_dict)

            # Remove MongoDB _id for return
            saved_conflicts.append({
                "conflict_id": conflict.conflict_id,
                "case_id": case_id,
                "agents_involved": agents_involved,
                "issue": issue,
                "description": description,
                "status": "unresolved"
            })

        return saved_conflicts
