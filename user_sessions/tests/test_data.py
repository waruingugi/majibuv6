mock_compoze_quiz_return_data = [
    {
        "id": "11f64cd1-2dfe-407d-bbe4-b0d0d3f7ec8e",
        "question_text": "What is the capital of France?",
        "choices": [
            {
                "id": "1018090e-d11f-4922-99a9-7966e84baaf9",
                "question_id": "11f64cd1-2dfe-407d-bbe4-b0d0d3f7ec8e",
                "choice_text": "London",
            },
            {
                "id": "da7e5187-8efa-43c7-b2ed-ae108e18c77b",
                "question_id": "11f64cd1-2dfe-407d-bbe4-b0d0d3f7ec8e",
                "choice_text": "Paris",
            },
        ],
    },
    {
        "id": "58d64a90-0166-4f4d-aa53-0eed88361274",
        "question_text": "What is 2+2?",
        "choices": [
            {
                "id": "3387f156-6749-4f9e-80ee-b06fa3794573",
                "question_id": "58d64a90-0166-4f4d-aa53-0eed88361274",
                "choice_text": "22",
            },
            {
                "id": "108d36f2-d708-4a6c-ba09-e65de1c0f6e8",
                "question_id": "58d64a90-0166-4f4d-aa53-0eed88361274",
                "choice_text": "4",
            },
        ],
    },
]


mock_paired_duo_session_details = {
    "id": "21162f8c-92be-4f13-be92-fded525f63ed",
    "category": "FOOTBALL",
    "status": "PAIRED",
    "party_a": {
        "username": "testuser2",
        "phone_number": "+25471****781",
        "score": 75.0,
        "total_answered": 4,
        "total_correct": 2,
        "questions": [
            {
                "question": "What is the chemical symbol for water?",
                "choice": "HVO",
                "is_correct": False,
            }
        ],
    },
    "party_b": {
        "username": "testuser",
        "phone_number": "+25471****678",
        "score": 0.0,
        "total_answered": 0,
        "total_correct": 0,
        "questions": [
            {
                "question": "What is the chemical symbol for water?",
                "choice": "H2O",
                "is_correct": True,
            }
        ],
    },
}


mock_refunded_duo_session_details = {
    "id": "21162f8c-92be-4f13-be92-fded525f63ed",
    "category": "FOOTBALL",
    "status": "PAIRED",
    "party_a": {
        "username": "testuser2",
        "phone_number": "+25471****781",
        "score": 75.0,
        "total_answered": 4,
        "total_correct": 2,
        "questions": [
            {
                "question": "What is the chemical symbol for water?",
                "choice": "HVO",
                "is_correct": False,
            }
        ],
    },
    "party_b": {},
}
