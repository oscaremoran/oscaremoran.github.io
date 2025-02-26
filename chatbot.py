def math_chatbot():
    print("Welcome to the Math Chatbot!")
    print("Start your question with: A (addition), S (subtraction), M (multiplication), D (division)")
    print("Format: [letter] number1 number2 (e.g., 'A 5 3' or 'S 10 2')")
    print("Type 'quit' to exit.")

    while True:
        user_input = input("Ask me a math question: ").strip()

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        # Split input into parts
        parts = user_input.split()
        if len(parts) != 3:
            print("Please use the format: [letter] number1 number2")
            continue

        operation, num1, num2 = parts[0].upper(), parts[1], parts[2]

        # Check if numbers are valid
        try:
            num1 = float(num1)
            num2 = float(num2)
        except ValueError:
            print("Please enter valid numbers!")
            continue

        # Perform the operation based on the starting letter
        if operation == "A":
            result = num1 + num2
            print(f"{num1} + {num2} = {result}")
        elif operation == "S":
            result = num1 - num2
            print(f"{num1} - {num2} = {result}")
        elif operation == "M":
            result = num1 * num2
            print(f"{num1} * {num2} = {result}")
        elif operation == "D":
            if num2 == 0:
                print("Cannot divide by zero!")
            else:
                result = num1 / num2
                print(f"{num1} / {num2} = {result}")
        else:
            print("Start with A, S, M, or D for an operation!")

# Run the chatbot
math_chatbot()