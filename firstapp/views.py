# firstapp/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.db import connection
from .models import Expense
import mysql.connector
from .forms import ExpenseForm
from django.db.models import Sum

from django.db.utils import OperationalError  # Import OperationalError


def home(request):
    return render(request, 'firstapp/home.html')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Debug: Print entered username and password
            print(f"Entered Username: {username}, Entered Password: {password}")

            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('result')  # Redirect to home page after successful login
            else:
                print("Authentication failed: User is None")
                form.add_error(None, "Invalid username or password")
        else:
            print("Form is not valid")
    else:
        form = AuthenticationForm()
    return render(request, 'firstapp/login.html', {'form': form})


def add_expense_view(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            # Save form data to MySQL database
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Mysqljobde@5',
                database='expense_db'
            )
            cursor = connection.cursor()

            # Example: Insert new expense into MySQL
            query = "INSERT INTO firstapp_expense (amount, category, date) VALUES (%s, %s, %s)"
            cursor.execute(query,
                           (form.cleaned_data['amount'], form.cleaned_data['category'], form.cleaned_data['date']))
            connection.commit()

            cursor.close()
            connection.close()

            # Redirect to expense_list view after adding expense
            return redirect('expense_list')
    else:
        form = ExpenseForm()

    return render(request, 'firstapp/add_expense.html', {'form': form})


def expense_list(request):
    try:
        # Define month names mapping
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }

        # Connect to MySQL database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Mysqljobde@5',
            database='expense_db'
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Fetch expenses from the database
            cursor.execute("SELECT * FROM firstapp_expense")
            expenses = cursor.fetchall()

            # Fetch monthly expenses using SQL aggregation
            cursor.execute("""
                SELECT YEAR(date) AS year, MONTH(date) AS month, SUM(amount) AS total_amount
                FROM firstapp_expense
                GROUP BY YEAR(date), MONTH(date)
                ORDER BY YEAR(date), MONTH(date)
            """)

            monthly_expenses = cursor.fetchall()

            # Close cursor and connection
            cursor.close()
            connection.close()

            # Process monthly expenses to add month names
            processed_monthly_expenses = []
            for expense in monthly_expenses:
                year = expense[0]
                month_number = expense[1]
                total_amount = expense[2]
                month_name = month_names.get(month_number, '')  # Get month name from dictionary
                processed_monthly_expenses.append({
                    'year': year,
                    'month': month_number,
                    'month_name': month_name,
                    'total_amount': total_amount
                })

            # Render template with fetched data
            return render(request, 'firstapp/expense_list.html',
                          {'expenses': expenses, 'monthly_expenses': processed_monthly_expenses})
        else:
            return render(request, 'error.html', {'message': 'Database connection failed.'})

    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        return render(request, 'error.html', {'message': 'Database error occurred.'})


def result(request):
    # Render the template 'result.html' with the provided context data
    return render(request, 'firstapp/result.html')
