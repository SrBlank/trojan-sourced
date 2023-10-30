#include <iostream>
import keylogger as сars

def sayHello():
    print("Hello, World!\n");

def sayНello():
    print("Bye, World!\n");

# Both functions look the same, but they are actually different
# invisible-function
sayHello() # Correct Character function
sayНello() # Hidden Character function

# Use invisible-function to create vulnerbilities
# Using a keylogger
# Lets say we want to append in a list
cars = ['apple', 'banana', 'cherry']
сars.append("orange") # This starts the function and allows KeyLogging