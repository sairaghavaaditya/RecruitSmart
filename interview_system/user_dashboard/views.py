from django.http import JsonResponse
import random
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Response, Question

from .models import User


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from admin_dashboard.models import JobPost
from .serializers import JobPostSerializer


class JobPostListView(APIView):
    def get(self, request):
        # Fetch only active jobs
        jobs = JobPost.objects.filter(is_active=True).order_by('-created_at')
        serializer = JobPostSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)




def fetch_question(request):
    try:
        # Fetch all questions
        questions = Question.objects.all()

        if not questions.exists():
            return JsonResponse({"error": "No questions available."}, status=404)

        # Log the available difficulty levels in the database
        difficulties = questions.values_list('difficulty', flat=True).distinct()
        print("Available difficulties:", difficulties)

        # Randomly select a difficulty level
        random_difficulty = random.choice(list(difficulties))
        print("Selected difficulty:", random_difficulty)

        # Filter questions by the selected difficulty
        filtered_questions = questions.filter(difficulty=random_difficulty)

        if not filtered_questions.exists():
            return JsonResponse({"error": "No questions available for the selected difficulty."}, status=404)

        # Get a random question
        question = random.choice(filtered_questions)

        # Ensure you're using the correct field names
        return JsonResponse({
            "id": question.id,
            "question": question.question,  # Replace 'question' with the correct field name if different
            "answer": question.answer,
            "difficulty": question.difficulty,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


from django.core.exceptions import ObjectDoesNotExist

def fetch_next_question(request):
    """
    Fetch the next question sequentially.
    Pass the `current_question_id` in the query parameter to get the next question.
    """
    try:
        # Get current question ID from the query parameter
        current_question_id = request.GET.get('current_question_id')

        # Fetch the next question
        if current_question_id:
            try:
                next_question = Question.objects.filter(id__gt=current_question_id).order_by('id').first()
            except ObjectDoesNotExist:
                next_question = None
        else:
            # Start with the first question if no ID is provided
            next_question = Question.objects.order_by('id').first()

        if not next_question:
            return JsonResponse({"message": "No more questions available."}, status=200)

        # Return the question data
        return JsonResponse({
            "id": next_question.id,
            "question": next_question.question,
            "answer": next_question.answer,
            "difficulty": next_question.difficulty,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



@csrf_exempt
def submit_response(request):
    if request.method == "POST":
        print("Submit response view called!")  # Debug statement
        try:
            data = json.loads(request.body)
            print("Received data:", data)  # Debug statement
            question_id = data.get("question_id")
            user_answer = data.get("user_answer")

            # Validate input
            if not question_id or not user_answer:
                return JsonResponse({"error": "Invalid input."}, status=400)

            # Fetch the corresponding question
            question = Question.objects.get(id=question_id)

            # Store the response in the database
            response = Response.objects.create(
                question=question,
                user_answer=user_answer,
            )
            print("Response saved:", response)  # Debug statement

            return JsonResponse({"message": "Response submitted successfully!"})

        except Question.DoesNotExist:
            return JsonResponse({"error": "Question not found."}, status=404)
        except Exception as e:
            print("Error:", str(e))  # Debug statement
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)




@csrf_exempt
def user_signup(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Parse JSON body
            first_name = data.get("firstName")
            last_name = data.get("lastName")
            mobile_number = data.get("mobileNumber")
            email = data.get("email")
            password = data.get("password")
            confirm_password = data.get("confirmPassword")

            # Check if all required fields are present
            if not all([first_name, last_name, mobile_number, email, password, confirm_password]):
                return JsonResponse({"error": "All fields are required."}, status=400)

            if password != confirm_password:
                return JsonResponse({"error": "Passwords do not match."}, status=400)

            # Check if the email already exists
            if User.objects.filter(email=email).exists():
                return JsonResponse({"error": "Email already registered."}, status=400)

            # Create the user
            User.objects.create(
                first_name=first_name,
                last_name=last_name,
                mobile_number=mobile_number,
                email=email,
                password=password,
            )

            return JsonResponse({"message": "Signup successful!"}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)







@csrf_exempt
def user_login(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            email = data.get("email")
            password = data.get("password")

            # Validate input
            if not email or not password:
                return JsonResponse({"error": "Email and password are required."}, status=400)

            # Check if the user exists
            try:
                user = User.objects.get(email=email)
                if user.password != password:  # Ideally, use a password hashing mechanism
                    return JsonResponse({"error": "Invalid email or password."}, status=401)
            except User.DoesNotExist:
                return JsonResponse({"error": "Invalid email or password."}, status=401)

            # Login successful
            return JsonResponse({"message": "Login successful!"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)

