import ast
import operator
from functools import reduce
from typing import Any, Dict, Optional

from tests_app.models import Question


class AnswerEvaluator:
    """Utility class for evaluating test answers"""

    @staticmethod
    def parse_numbers(text: str) -> list:
        """Parse numbers from question text safely"""
        try:
            return ast.literal_eval(text)
        except (ValueError, SyntaxError):
            raise ValueError("Invalid question format")

    @classmethod
    def calculate_answer(cls, question: Question):
        """Calculate the correct answer for a question"""
        try:
            numbers = cls.parse_numbers(question.text)

            operations = {
                Question.QuestionType.PLUS: sum,
                Question.QuestionType.MULTIPLY: lambda x: reduce(
                    operator.mul, x
                ),
                Question.QuestionType.DIVIDE: lambda x: round(x[0] / x[1], 2),
            }

            if question.question_type not in operations:
                return None

            return operations[question.question_type](numbers)

        except (ValueError, SyntaxError, TypeError):
            return None

    @classmethod
    def format_answer(cls, answer: Any, question_type: str) -> str:
        """Format the answer based on question type"""
        if answer is None:
            return None

        if question_type == Question.QuestionType.DIVIDE:
            return str(round(float(answer), 2))
        return str(answer)

    @classmethod
    def parse_student_answer(cls, answer_text: str, question_type: str) -> Any:
        """Parse and format student answer based on question type"""
        try:
            if question_type == Question.QuestionType.DIVIDE:
                return round(float(answer_text), 2)
            return int(answer_text)
        except (ValueError, TypeError):
            raise ValueError("Invalid answer format")

    @classmethod
    def evaluate_answer(
        cls, question: Question, answer_text: str
    ) -> Dict[str, Any]:
        """Evaluate student's answer for a given question"""
        try:
            # Calculate expected answer
            expected_answer = cls.calculate_answer(question)
            if expected_answer is None:
                return {
                    "is_correct": False,
                    "marks_obtained": 0,
                    "expected_answer": None,
                    "error": "Unsupported question type",
                }

            # Parse student's answer
            student_answer = cls.parse_student_answer(
                answer_text, question.question_type
            )

            # Compare answers
            is_correct = student_answer == expected_answer
            marks_obtained = question.marks if is_correct else 0

            return {
                "is_correct": is_correct,
                "marks_obtained": marks_obtained,
                "expected_answer": expected_answer,
                "student_answer": student_answer,
            }

        except ValueError as e:
            return {
                "is_correct": False,
                "marks_obtained": 0,
                "expected_answer": None,
                "error": str(e),
            }
        except Exception as e:  # NOQA
            return {
                "is_correct": False,
                "marks_obtained": 0,
                "expected_answer": None,
                "error": "An unexpected error occurred",
            }
