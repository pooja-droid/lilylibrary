# Import necessary modules and libraries
from flask import Flask, render_template, redirect, url_for, session, flash, request, send_file, abort
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, PasswordField, SelectField, TextAreaField, RadioField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, Optional, ValidationError
import sqlite3
import random
import string
import numpy as np
import datetime
from datetime import date
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Create a Flask application instance
app = Flask(__name__, static_folder="/Users/poojagada/VS Code Projects/Lily Library NEA/static")
# Set a secret key to prevent CSRF (Cross-Site Request Forgery) attacks 
app.config["SECRET_KEY"] = "afreiluo4389" 

# Define program constants

# Defines the filepath of the SQLite databse file the system will be interacting with. 

DBNAME = "library.db"

# Defines a binary key value for XOR operations in the hashing algorithm
BINKEY = "000101001100"

# Defines an admin code for the system. Will be used to check if a reader has admin permissions and will determine what tasks they can perform on the system.
ADMINCODE = "57493"

# Defines a Database class to contain operations that are performed on the database
class Database():
    
    # Constructor for the Database class
    # Takes the filename of the SQLite database file as a parameter
    def __init__(self, dbName):
        self.dbName = dbName
    
    # Method to establish a connection to the SQLite database
    # Creates a cursor object to allow the execution of SQL queries
    def connect(self):
        self.con = sqlite3.connect(self.dbName)
        self.cur = self.con.cursor()
    
    # Method to execute parameterised SQL queries
    # Takes the query to execute and optional parameters to pass to the query as parameters
    def execute(self, query, params=()):
        self.cur.execute(query, params)
        
    # Method to fetch a single row from the result of the last query execution
    # Returns a tuple containing the result
    def fetchOne(self):
        return self.cur.fetchone()
    
    # Method to fetch all the rows from the result of the last query execution
    # Returns a list of tuples containing results
    def fetchAll(self):
        return self.cur.fetchall()
    
    # Method to fetch a specified number of rows from the result of the last query execution
    # Takes desired number of results to be returned as a parameter
    # Returns a list of tuples containing results
    def fetchMany(self, size):
        return self.cur.fetchmany(size)
    
    # Method to get the ID/Primary Key value of the last inserted row
    def getLastRowID(self):
        return self.cur.lastrowid
    
    # Method to commit changes to the database
    def commit(self):
        self.con.commit()
    
    # Method to close the connection to the SQLite database
    def close(self):
        self.con.close()

# Defines a User class
class User():
     
    #  Constructor for the User class
    def __init__(self):
        pass
    
    # Method to generate a random salt for a given username
    # Takes the username as a parameter and returns a random string the length of the username as the salt
    def getSalt(self, username):
        length = len(username)
        characters = string.ascii_letters + string.digits + string.punctuation
        salt = "".join(random.choice(characters) for i in range(length))
        return salt

    def getChunks(self, password, salt):
        # Append the salt to the password
        # Pad the password with 0s until its length is a multiple of 4, so that chunks are equal length
        password = password + salt
        while len(password) % 4 != 0: 
            password += "0"
        
        # Convert every character in password to Unicode numerical representation
        chars = []
        for char in password:
            chars.append(ord(char))
        # Split the list of numbers into a list of lists of length 4
        chunks = [chars[i:i+4] for i in range(0, len(chars)-3, 4)]
        return chunks

    def getBinaryChunks(self, chunks):
        binaryChunks = []
        # Sum each chunk and convert it into its 12 digit binary representation
        for chunk in chunks:
            binaryChunk = "{0:012b}".format(np.sum(chunk))
            binaryChunks.append(binaryChunk)
        return binaryChunks

    def getXORChunks(self, binaryChunks, binkey):
        xorChunks = []
        # XOR each bianry chunk with the key
        for chunk in binaryChunks:
            xorChunks.append(int(chunk, 2) ^ int(binkey, 2))
        return xorChunks
    
    def processChunks(self, chunks):
        # Base case: if only 1 chunk left return the sum of that chunks
        if len(chunks) == 1:
            return sum(chunks)
        else:
        # Split chunks into half and recursively call method on each half
            mid = len(chunks) // 2
            left_sum = self.processChunks(chunks[:mid])
            right_sum = self.processChunks(chunks[mid:])
        # Perform multiplication on chunks and mod to produce a number
            return (left_sum * right_sum) % 1000000 

    def getHash(self, password, salt, key):
        # Call the methods to generate a unique hash value for each password, mod the hash value by 1000 to limit its size
        chunks = self.getChunks(password, salt)
        binaryChunks = self.getBinaryChunks(chunks)
        xorChunks = self.getXORChunks(binaryChunks, key)
        hash = self.processChunks(xorChunks)
        return hash % 1000


# Defines a UserManagement class that contains methods related to the User class
class UserManagement():
    
    # Constructor for the UserManagement class
    # Takes an instance of the Reader class as a parameter
    # Takes the filename of the SQLite database file as a parameter
    def __init__(self, reader, dbName):
        self.db = Database(dbName)
        self.reader = reader
    
    # Method that checks if the passed-in personal and school email addresses exist in the database. If they do return True, else return False
    # Method used in allowing user to change their password if they exist as a valid user
    def checkEmail(self, personalemailaddress, schoolemailaddress):
        self.db.connect()
        self.db.execute("SELECT * FROM Reader WHERE SchoolEmailAddress = ? AND PersonalEmailAddress = ?", (schoolemailaddress, personalemailaddress))
        if self.db.fetchOne():
            self.db.close()
            return True
        else:
            self.db.close()
            return False
    
    # Method that allows a user to change their personal email address
    def checkSchoolEmail(self, personalemailaddress, schoolemailaddress):
        self.db.connect()
        query = "SELECT * FROM Reader WHERE SchoolEmailAddress = ?"
        params = (schoolemailaddress, )
        self.db.execute(query, params)
        result = self.db.fetchOne()
        # Checks is they have a valid school email address that already exists in the database, and if so allows them to change it, otherwise, returns False
        if result:
            query2 = "UPDATE Reader SET PersonalEmailAddress = ? WHERE ReaderID = ?"
            params2 = (personalemailaddress, self.reader.readerID)
            self.db.execute(query2, params2)
            self.db.commit()
            self.db.close()
            return True
        else:
            self.db.close()
            return False
    
    # Method that allows a reader to change their current password
    # Takes the new password as a parameter, retrieves the salt for that reader and hashes the password, before storing it in the database
    def changePassword(self, password):
        self.db.connect()
        readerID = self.reader.readerID
        self.db.execute("SELECT ReaderSalt FROM READER WHERE ReaderID = ?", (readerID, ))
        salt = self.db.fetchOne()[0]
        hash = self.reader.getHash(password, salt, BINKEY)
        self.db.execute("UPDATE READER SET ReaderHash = ? WHERE ReaderID = ?", (hash, readerID))
        self.db.commit()
        self.db.close()   
    
    # Method to validate a password according to specified requirements
    def passwordValidator(self, form, field):
        password = field.data
        # Takes password entered into a password field in the RegistrationForm class by the user and matches it against a regular expression that checks if it has at least 1 uppercase letter, 1 lowercase letter, 1 digit, 1 special character from a provided set and is between 4-15 characters in length
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*&])[A-Za-z\d@$!%*?&]{4,15}$'
        # If the password matches the regular expression it is validated and the user is registered
        # If the password doesn't match a Validation Error appears on the website and the user must re-enter a new password to register
        if not re.match(pattern, password):
            raise ValidationError("Password doesn't match specified requirements.")
    
    # Method to validate a personal email address
    def personalEmailValidator(self, form, field):
        # Takes the email entered into an email field in the RegistrationForm class and checks whether it follows an email structure of characters followed by an @ symbol followed by more characters signifying an organisation name followed by a domain ending
        email = field.data
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # If the email matches, the user is allowed to proceed, if not a Validation Error is raised and the user is prompted to re-enter a valid personal email
        if not re.match(pattern, email):
            raise ValidationError("Not a valid email address.")
    
    # Method to validate a school email address
    def schoolEmailValidator(self, form, field):
        email = field.data
        # Checks if the email matches a regular expression defining characters followed by @mcsoxford.org
        pattern = r'.*@mcsoxford\.org$'
        # If so, user may proceed, if not Validation Error raised and user prompted to re-enter email to register
        if not re.match(pattern, email):
            raise ValidationError("Not a valid school email address.")

# Defines a Reader class that inherits from the User class           
class Reader(User):
    
    # Constructor for Reader class, inherits the constructor of the User class
    # Takes the filename of the SQLite database file as a parameter
    # Initialises a class variable readerID to 0, which will be overwritten later
    def __init__(self, dbName):
        super().__init__()
        self.db = Database(dbName)
        self.readerID = 0
    
    # Method that gets a readerID based on the session['username'] once a reader has logged in, and sets the class variable self.readerID to this value
    def setAndGetReaderID(self, username):
        self.db.connect()
        self.db.execute("SELECT ReaderID FROM Reader WHERE ReaderUsername = ?", (username, ))
        readerID = self.db.fetchOne()
        self.db.close()
        if readerID:
            self.readerID = readerID[0]
            return self.readerID
        
    # Method to register a new reader
    def registerNewReader(self, firstname, lastname, username, password, schoolemailaddress, personalemailaddress, dateofbirth, yeargroup, houseroom, admincode):
        self.db.connect()
        # Takes entered reader information from RegistrationForm and inserts a new record into the Reader table in the database
        # If they have attempted to enter an admin code, if it is correct and matches the ADMINCODE constant, they are given librarian permissions, and if it is incorrect the method returns 0 and they are prevented from registering
        if (admincode == None) or (admincode == ADMINCODE):
            query = "INSERT INTO Reader (FirstName, LastName, ReaderUsername, ReaderSalt, ReaderHash, SchoolEmailAddress, PersonalEmailAddress, DateOfBirth, YearGroup, Houseroom, AdminCode) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            salt = self.getSalt(username)
            hash = self.getHash(password, salt, BINKEY)
            yeargroup = int(yeargroup)
            self.db.execute(query, (firstname, lastname, username, salt, hash, schoolemailaddress, personalemailaddress, dateofbirth, yeargroup, houseroom, admincode))
            self.db.commit()
            self.db.close()
        else:
            self.db.close()
            return 0

    # Method to log in a reader
    def loginReader(self, password, admincode):
        # Takes password of the reader and an optional admin code if they login as a librarian
        self.db.connect()
        # Try to retrieve a reader from the database whose readerID matches the readerID set when the reader logins in with their username
        self.db.execute("SELECT ReaderSalt, ReaderHash FROM Reader WHERE ReaderID = ?", (self.readerID,))
        row = self.db.fetchOne()
        self.db.close()
        # If no such reader exists, a 'Wrong username' method is displayed to the user on the screen 
        # If the reader exists and the admin code is provided but not correct a 'Wrong admin code' message is displayed to the user
        # If the admin code is none or is correct but the password provided doesn't hash to the same stored ReaderHash value, a 'Wrong password' message is displayed, else the reader is successfully logged in
        if row:
            salt, retrievedHash = row
            if (admincode == None) or (admincode == ADMINCODE):
                hash = self.getHash(password, salt, BINKEY)
                if (hash == int(retrievedHash)):
                    return 1
                else:
                    return flash("Wrong password")
            else:
                return flash("Wrong admin code")
        else:
            return flash("Wrong username")

    # Method to ge the current account details of a reader
    def getCurrentAccountDetails(self, readerID=None):
        self.db.connect()
        query = """SELECT FirstName, LastName, ReaderUsername, SchoolEmailAddress, PersonalEmailAddress, YearGroup, Houseroom FROM Reader WHERE ReaderID = ?"""
        # If no readerID is provided, the session['readerID'] value is used, which shows a reader their own current account details
        # However, when the librarian is managing account information, if a particular reader is selected their readerID is passed to this method, and then the account information for that reader is retrieved instead of the account information for the librarian themself
        if readerID is not None:
            params = (readerID, )
        else:
            params = (self.readerID, )
        self.db.execute(query, params)
        accountDetails = self.db.fetchOne()
        self.db.close()
        return accountDetails 
    
    # Method to update the account details of a reader
    def updateAccountDetails(self, readerID, firstname=None, lastname=None, username=None, personalemail=None, schoolemail=None, yeargroup=None, houseroom=None):
        self.db.connect()
        query = "UPDATE Reader SET "
        params = []
        # The if block for whichever parameters are passed in will run and will append the clause updating that parameter to the query and will append that parameter to params
        if firstname is not None:
            query += "FirstName = ?, "
            params.append(firstname)

        if lastname is not None:
            query += "LastName = ?, "
            params.append(lastname)

        if username is not None:
            query += "ReaderUsername = ?, "
            params.append(username)

        if personalemail is not None:
            query += "PersonalEmailAddress = ?, "
            params.append(personalemail)

        if schoolemail is not None:
            query += "SchoolEmailAddress = ?, "
            params.append(schoolemail)

        if yeargroup is not None:
            query += "YearGroup = ?, "
            params.append(yeargroup)

        if houseroom is not None:
            query += "Houseroom = ?, "
            params.append(houseroom)

        # Remove the trailing comma and whitespace after the last clause is appended
        query = query.rstrip(', ')

        query += " WHERE ReaderID = ?"
        params.append(readerID)
        params = tuple(params)
        self.db.execute(query, params)
        self.db.commit()
        self.db.close()
        
    # Method to retrieve information from Reader and Loan tables in order to create a leaderboard
    def getLeaderboard(self):
        # Retrieves readers with the most loans taken out that month, and orders them in descending order of number of loans
        self.db.connect()
        query = """SELECT Reader.ReaderUsername, CASE 
          WHEN Reader.YearGroup = 0 THEN 'Staff'
          WHEN Reader.YearGroup = 1 THEN 'Librarian'
          ELSE 'Year ' || CAST(Reader.YearGroup AS TEXT)
      END AS YearGroupLabel, COUNT(Loan.LoanID) AS LoanCount FROM Loan INNER JOIN Reader ON Loan.ReaderID = Reader.ReaderID WHERE strftime('%m', Loan.LoanStartDate) = strftime('%m', 'now') GROUP BY Loan.ReaderID ORDER BY LoanCount DESC"""
        params = ()
        self.db.execute(query, params)
        # Returns list of tuples containing the readers' username, year group and number of loans
        leaderboard = self.db.fetchAll()
        self.db.close()
        return leaderboard
    
    # Method to allow librarians to search for a reader based on just a name string
    def searchReader(self, name):
        self.db.connect()
        # The reader's first and last names are concatenated and are checked to see if they contain the entered string
        query = """SELECT ReaderID, FirstName, LastName, YearGroup, Houseroom FROM Reader WHERE FirstName || ' ' || LastName LIKE '%' || ? || '%'"""
        params = (name, )
        self.db.execute(query, params)
        readers = self.db.fetchAll()
        self.db.close()
        return readers
    
    # Method to allow librarian to delete a reader from the database
    # Takes the ID of the reader to be deleted as a parameter
    def deleteReader(self, readerID):
        self.db.connect()
        query = """DELETE FROM Reader WHERE ReaderID = ?"""
        params = (readerID, )
        self.db.execute(query, params)
        self.db.commit()
        self.db.close()

# Defines a ReadingList class
class ReadingList():
    
    # Constructor for the ReadingList class
    # Takes the filename of the SQLite database file as a parameter
    def __init__(self, dbName):
        self.db = Database(dbName)
    
    # Method to retrieve all the reading lists and the books they contain for a given reader
    def getReadingLists(self, readerID):
        self.db.connect()
        query = """SELECT ReadingList.ReadingListTitle, Book.BookID, CASE
        WHEN ReadingListBook.Read = 1 THEN 'Read'
        WHEN ReadingListBook.Read = 0 THEN 'WanttoRead'
        END AS Status, Book.CoverImageURL FROM ReadingList INNER JOIN ReadingListBook ON ReadingList.ReadingListID = ReadingListBook.ReadingListID INNER JOIN Book ON ReadingListBook.BookID = Book.BookID WHERE ReadingList.ReaderID = ?"""
        params = (readerID, )
        self.db.execute(query, params)
        # Returns reading list title, book id, whether the book was read, and the cover image for every row in ReadingListBook that has the specified readerID
        readingLists = self.db.fetchAll()
        self.db.close()
        # Collates the results into a dictionary where the key is the reading list title and the value is a list of tuples of books that are in that reading list
        organisedLists = {}
        for row in readingLists:
            title = row[0]
            bookID = row[1]
            status = row[2]
            coverImage = row[3]
            if title not in organisedLists:
                organisedLists[title] = []
            organisedLists[title].append((bookID, status, coverImage))
        return organisedLists
    
    # Method to retrieve any previously created reading lists by a given reader
    # Called in the Reading List Form to popualte the choices attribute of the reading list title field so that a reader has the choice to add a book to a new reading list or a previously created list
    def getReadingListChoices(self, readerID):
        self.db.connect()
        self.db.execute("SELECT DISTINCT ReadingListTitle FROM ReadingList WHERE ReadingList.ReaderID = ?", (readerID, ))
        readingListsTitleTuples = self.db.fetchAll()
        readingListChoices = []
        for i in range(0, len(readingListsTitleTuples)):
            readingListChoices.append((readingListsTitleTuples[i][0], readingListsTitleTuples[i][0]))
        self.db.close()
        return readingListChoices
    
    # Method to add a book to an existing reading list for a given reader
    def addToExistingReadingList(self, readerID, choice, bookID, read):
        self.db.connect()
        query = "SELECT ReadingListID From ReadingList WHERE ReadingListTitle = ? AND ReaderID = ?"
        params = (choice, readerID)
        self.db.execute(query, params)
        readinglistID = self.db.fetchOne()[0]
        query2 = """INSERT INTO ReadingListBook VALUES (?, ?, ?)"""
        params2 = (readinglistID, bookID, int(read))
        self.db.execute(query2, params2)
        self.db.commit()
        self.db.close()
    
    # Method to add a book to a new reading list for a given reader
    def addToNewReadingList(self, readerID, title, bookID, read):
        self.db.connect()
        query = "INSERT INTO ReadingList (ReaderID, ReadingListTitle) VALUES (?, ?)"
        params = (readerID, title)
        self.db.execute(query, params)
        self.db.commit()
        query2 = "INSERT INTO ReadingListBook VALUES ((SELECT ReadingListID FROM ReadingList WHERE ReadingListTitle = ?), ?, ?)"
        params2 = (title, bookID, read)
        self.db.execute(query2, params2)
        self.db.commit()
        self.db.close()
    
    # Method to retrieve all the reading lists a book appears in
    # Returns a list of reading list titles for a given book that are displayed on its book page to inform reader how other readers have categorised the book
    def getReadingListsForBook(self, bookID):
        self.db.connect()
        query = """SELECT ReadingList.ReadingListTitle FROM ReadingList INNER JOIN ReadingListBook ON ReadingList.ReadingListID = ReadingListBook.ReadingListID INNER JOIN Book ON ReadingListBook.BookID = Book.BookID WHERE Book.BookID = ?"""
        params = (bookID, )
        self.db.execute(query, params)
        readingListTags = self.db.fetchAll()
        self.db.close()
        return readingListTags

# Defines a Review class
class Review():
    
    # Constructor for the Review class
    # Takes the filename of the SQLite database file as a parameter
    def __init__(self, dbName):
        self.db = Database(dbName)
    
    # Method to retrieve all the reviews left by a reader
    # Takes readerID as a parameter and returns a list of tuples containing review information
    def getReaderReviews(self, readerID):
        self.db.connect()
        query = """
        SELECT Review.ReviewText, Review.Rating, Review.DateReviewed, Book.BookID, Book.CoverImageURL FROM Review INNER JOIN Book ON Review.BookID = Book.BookID WHERE Review.ReaderID = ? ORDER BY Review.DateReviewed DESC
        """
        params = (readerID, )
        self.db.execute(query, params)
        readerReviews = self.db.fetchAll()
        self.db.close()
        return readerReviews
    
    # Method to get all the reviews for a particular book
    # Takes a bookID as a parameter and returns a list of tuples and a dictionary
    def getBookReviews(self, bookID):
        self.db.connect()
        query = """
        SELECT Review.ReviewText, Review.Rating, Review.DateReviewed, Reader.FirstName, Reader.LastName FROM Review INNER JOIN Reader ON Review.ReaderID = Reader.ReaderID WHERE Review.BookID = ?
        """
        params = (bookID, )
        self.db.execute(query, params)
        # bookReviews contains the review text, rating, date reviewed, reader's first name, and last name.
        bookReviews = self.db.fetchAll()
        if len(bookReviews) == 0:
            return [], {}
        
        # The dictionary ratingsCount contains the percentage distribution of ratings for that book, created by counting the number of reviews of 1, 2, 3, 4, and 5 stars and dividing it by the total number of reviews
        ratingsCount = {i: sum(1 for review in bookReviews if review[1] == i) for i in range(1, 6)}
        numberOfReviews = len(bookReviews)
        ratingPercentage = {i: (count / numberOfReviews) * 100 for i, count in ratingsCount.items()}
        self.db.close()
        return bookReviews, ratingPercentage
    
    # Method to allow a reader to leave a review for a book
    # Takes bookID, readerID, review content and the rating as parameters and inserts this information into the Review table  
    def leaveReview(self, readerID, reviewtext, rating, bookID):
        self.db.connect()
        dateNow = date.today()
        query2 = "INSERT INTO Review (BookID, ReaderID, ReviewText, Rating, DateReviewed) VALUES (?, ?, ?, ?, ?)"
        params2 = (bookID, readerID, reviewtext, rating, dateNow)
        self.db.execute(query2, params2)
        self.db.commit()
        self.db.close()

# Defines a Book class
class Book():
    
    # Constructor for the Book class
    # Takes the filename of the SQLite database file as a parameter
    # Takes an instance of the NotificationManager class as a parameter
    def __init__(self, notificationManager, dbName):
        self.notificationManager = notificationManager
        self.db = Database(dbName)
    
    # Method that allows a reader to search for books by two methods
    def searchBook(self, orderByField, orderByDirection, searchString=None, authorFirstName=None, authorLastName=None, bookTitle=None, bookISBN=None, bookGenre=None):
        self.db.connect()
        # The reader can specify whether they would like the results to be ordered by a particular field in a particular direction and these values will be passed as parameters to either query otherwise the results are ordered by title in ascending order by default
        if not orderByDirection:
                orderByDirection = "ASC"
        if not orderByField:
            orderByField = "Title"
        # If the user has entered a search string, that is passed to an SQL query to retrieve all books whose title, genre, or author name matches that string
        if searchString:
            query = f"""
            SELECT Book.BookID, Book.Title, Book.CoverImageURL FROM Book INNER JOIN AuthorBook ON Book.BookID = AuthorBook.BookID INNER JOIN Author ON AuthorBook.AuthorID = Author.AuthorID WHERE LOWER(Author.AuthorFirstName) LIKE ? OR LOWER(Author.AuthorLastName) LIKE ? OR LOWER(Book.Title) LIKE ? OR LOWER(Book.Genre) LIKE ? AND Book.BookID NOT IN (
            SELECT BookID
            FROM BookCopy
            WHERE Status = 'Decommissioned'
        ) ORDER BY {orderByField} {orderByDirection}
            """
            params = tuple([f"%{searchString.lower()}%"] * 4)
            self.db.execute(query, params)
            searchResults = self.db.fetchAll()
            self.db.close()
            print(searchResults)
            return searchResults
        # Or the reader can also use advanced search functionality and search specifically by an author's first name, last name, book title, isbn or genre
        else:
            query = f"SELECT Book.BookID, Book.Title, Book.CoverImageURL FROM Book INNER JOIN AuthorBook ON Book.BookID = AuthorBook.BookID INNER JOIN Author ON AuthorBook.AuthorID = Author.AuthorID WHERE 1=1"
            params = ()
            print(authorFirstName)
            if authorFirstName:
                print("Author First Name:", authorFirstName)
                query += " AND LOWER(Author.AuthorFirstName) LIKE ?"
                params += (f"%{authorFirstName.lower()}%", )
            if authorLastName:
                print("Author Last Name:", authorLastName)
                query += " AND LOWER(Author.AuthorLastName) LIKE ?"
                params += (f"%{authorLastName.lower()}%", )
            if bookTitle:
                query += " AND LOWER(Book.Title) LIKE ?"
                params += (f"%{bookTitle.lower()}%", )
            if bookISBN:
                query += " AND LOWER(Book.ISBN) LIKE ?"
                params += (f"%{bookISBN.lower()}%", )
            if bookGenre:
                query += " AND LOWER(Book.Genre) LIKE ?"
                params += (f"%{bookGenre.lower()}%", )
            query += f""" AND Book.BookID NOT IN (
            SELECT BookID
            FROM BookCopy
            WHERE Status = 'Decommissioned' ) ORDER BY {orderByField} {orderByDirection}"""
            
            print(query)
            print(params)
            
            self.db.execute(query, params)
            searchResults = self.db.fetchAll()
            self.db.close()
            print(searchResults)
            return searchResults
    
    # Method to retrieve new books to the library
    # Takes in a date as a parameter, and returns any books added to the library after this date
    def getNewBooks(self, date):
        self.db.connect()
        query = """
        SELECT Book.BookID,
            CASE
                WHEN EXISTS (SELECT 1
                    FROM BookCopy
                    WHERE BookCopy.BookID = Book.BookID
                    AND BookCopy.Status = 'Available') THEN 'Available'
                ELSE 'On Loan'
            END AS BookStatus,
            Book.CoverImageURL
        FROM Book
        WHERE DateAdded >= ?
        AND Book.BookID NOT IN (
            SELECT BookID
            FROM BookCopy
            WHERE Status = 'Decommissioned'
        );
        """
        params = (date, )
        self.db.execute(query, params) 
        newBooks = self.db.fetchAll()
        self.db.close()
        return newBooks
    
    # Method to create and populate CSV file with the fields Title, Genre, AuthorName and PublisherName for all the books in the SQLite database
    def generateBooksCSV(self):
        self.db.connect()
        query = "SELECT Book.Title, Book.Genre, Author.AuthorFirstName || '' || Author.AuthorLastName, Publisher.PublisherName FROM Book INNER JOIN AuthorBook ON Book.BookID = AuthorBook.BookID INNER JOIN Author ON AuthorBook.AuthorID = Author.AuthorID INNER JOIN Publisher ON Book.PublisherID = Publisher.PublisherID"
        df = pd.read_sql(query, self.db.con)
        headers = ["Title", "Genre", "AuthorName", "PublisherName"]
        df.to_csv('librarybooks.csv', index=False, header=headers)
    
    # Method to build a recommendations algorithm
    def recommender(self, bookTitle):
        # Opens the created CSV file as a data frame, converts the Title and Publisher fields' data to lowercase
        df = pd.read_csv('librarybooks.csv', on_bad_lines='skip', sep=",")
        df['Title'] = df['Title'].str.lower()
        df['PublisherName'] = df['PublisherName'].str.lower()
        # Concatenates all the columns except the first index column into a single string separated by spaces
        df['data'] = df[df.columns[1:]].apply(
            lambda x: ' '.join(x.dropna().astype(str)),
            axis=1
        )
        # Then creates a matrix using the Count Vectorizer object whcih counts the frequency of each value in the entire file and converts them into a vector representation
        vectorizer = CountVectorizer()
        vectorized = vectorizer.fit_transform(df['data'])
        # Uses a cosine similarity function to find the angle between two vectors and applies this to every vector in vectorized, this will be based on the genre of the books their author, publisher or title
        similarities = cosine_similarity(vectorized)
        # Creates a new dataframe that has book title as the index and the title of all the other books as column with every value being the similarity between those two book titles
        df = pd.DataFrame(similarities, columns=df['Title'], index=df['Title']).reset_index()
        # Retrieves the top 6 most similar books to the parameter bookTitle and filters out bookTitle from this result
        recommendations = pd.DataFrame(df.nlargest(6, bookTitle)['Title'])
        recommendations = recommendations[recommendations['Title']!=bookTitle]
        # Returns a list of recommendations
        return recommendations['Title'].tolist()
    
    # Method to retrieve recommended books for a reader based on their past history by applying the recommendation algorithm
    def getRecommendedBooks(self, readerID):
        self.db.connect()
        # Retrieves the book titles of the reader's 5 most recent loans and the book titles of the 5 highest rated reviews left by the reader where the ratings are 3 stars or above.
        query = """SELECT Book.Title FROM Loan INNER JOIN Book ON Loan.BookID = Book.BookID WHERE Loan.ReaderID = ? ORDER BY LoanStartDate DESC"""
        params = (readerID, )
        self.db.execute(query, params)
        loanTitles = [result[0] for result in self.db.fetchMany(5)]  
        query2 = """SELECT Book.Title FROM Review INNER JOIN Book ON Review.BookID = Book.BookID WHERE Review.Rating >= 3 AND Review.ReaderID = ? ORDER BY Review.Rating DESC"""
        self.db.execute(query2, params)
        reviewTitles = [result[0] for result in self.db.fetchMany(5)]
        print(loanTitles, reviewTitles)
        # Calls the generateBooksCSV function to create the CSV file, before calling the recommender function on each title and adding the recommended titles to a recommendations list if they are not already in it
        self.generateBooksCSV()
        recommendations = []
        for title in loanTitles:
            recs = self.recommender(title.lower())
            for rec in recs:
                if rec not in recommendations:
                    recommendations.append(rec)
                    
        for title in reviewTitles:
            recs = self.recommender(title.lower())
            for rec in recs:
                if rec not in recommendations:
                    recommendations.append(rec)
        
        recommendedBooks = [] 
        # Retrieves book information for each recommended book 
        for title in recommendations:
            query3 = """SELECT Book.BookID,
            CASE
                WHEN EXISTS (SELECT 1
                    FROM BookCopy
                    WHERE BookCopy.BookID = Book.BookID
                    AND BookCopy.Status = 'Available')
                THEN 'Available'
                ELSE 'On Loan'
            END AS BookStatus,
            Book.CoverImageURL
            FROM Book
            WHERE LOWER(Title) = ? AND Book.BookID NOT IN (
                SELECT BookID
                FROM BookCopy
                WHERE Status = 'Decommissioned'
            );"""
            params3 = (title, )
            self.db.execute(query3, params3)
            book = self.db.fetchOne()
            recommendedBooks.append(book)
        self.db.close()
        # Returns recommended books
        return recommendedBooks

    # Method to get information about a given book
    def getBookInfo(self, bookID):
        # Takes BookID as a parameter and performs a cross-table query to retrieve information such as book title, genre, author, publisher etc. as well as counting the number of reviews for a book, and finding the average rating of a book and whether the book is available to be loaned or reserved
        self.db.connect()
        query = """
        SELECT Book.BookID, Book.ISBN, Book.Title, Book.Genre, Book.YearPublished, Publisher.PublisherName, Author.AuthorFirstName, Author.AuthorLastName, Book.Blurb, Book.CoverImageURL,
        (
            SELECT COUNT(*)
            FROM Review
            WHERE Review.BookID = Book.BookID
        ) AS NumberOfRatings, 
        (
            SELECT ROUND(AVG(Rating), 2)
            FROM Review
            WHERE Review.BookID = Book.BookID
        ) AS RatingAverage,
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM BookCopy
                WHERE BookCopy.BookID = Book.BookID
                AND BookCopy.Status = 'Available'
            ) THEN 'Loan Book'
            ELSE 'Reserve Book'
        END AS BookStatus 
    FROM Book INNER JOIN AuthorBook ON Book.BookID = AuthorBook.BookID INNER JOIN Author ON AuthorBook.AuthorID = Author.AuthorID INNER JOIN Publisher ON Book.PublisherID = Publisher.PublisherID WHERE Book.BookID = ? AND Book.BookID NOT IN (
            SELECT BookID
            FROM BookCopy
            WHERE Status = 'Decommissioned'
        );
        """
        params = (bookID, )
        self.db.execute(query, params)
        bookInfo = self.db.fetchAll()
        self.db.close()
        return bookInfo
    
    # Method to return all the books in a library that are in a particular genre
    # Takes book genre as a parameter and returns books whose Genre field contains that string
    def getBookInGenre(self, genre):
        self.db.connect()
        query = query = """
        SELECT Book.BookID,
            CASE
                WHEN EXISTS (SELECT 1
                    FROM BookCopy
                    WHERE BookCopy.BookID = Book.BookID
                    AND BookCopy.Status = 'Available')
                THEN 'Available'
                ELSE 'On Loan'
            END AS BookStatus,
            Book.CoverImageURL
        FROM Book
        WHERE LOWER(Genre) LIKE ? AND Book.BookID NOT IN (
            SELECT BookID
            FROM BookCopy
            WHERE Status = 'Decommissioned'
        );
        """
        genre = "%" + genre + "%"
        params = (genre, )
        self.db.execute(query, params)
        booksInGenre = self.db.fetchAll()
        self.db.close()
        return booksInGenre
    
    # Method to retrieve the most popular books in the library
    def getPopularBooks(self):
        self.db.connect()
        # Query retrieves the number of loans for each book in the library and orders the results by loan count descending, so the most popular books are first
        query = """SELECT Book.BookID, CASE 
        WHEN EXISTS (
            SELECT 1
            FROM BookCopy
            WHERE BookCopy.BookID = Loan.BookID
            AND BookCopy.Status = 'Available'
        ) THEN 'Available'
        ELSE 'On Loan'
    END AS BookStatus,
    Book.CoverImageURL,
    COUNT(*) AS LoanCount FROM Loan INNER JOIN 
    Book ON Loan.BookID = Book.BookID WHERE strftime('%m', LoanStartDate) = strftime('%m', 'now') AND Book.BookID NOT IN (
            SELECT BookID
            FROM BookCopy
            WHERE Status = 'Decommissioned'
        ) GROUP BY Loan.BookID, BookStatus ORDER BY LoanCount DESC;"""
        params = ()
        self.db.execute(query, params)
        popularBooks = self.db.fetchAll()
        self.db.close()
        return popularBooks
    
    # Method to delete a book from the library, if physical copy is missing or has been overdue for a long time
    # This is rare, so the book is not fully deleted as it could be retrieved at a later date
    def deleteBook(self, bookID):
        # The BookCopy status is updated to decommissioned so it will no longer appear in query results from the database and will in effect be inaccessible to readers
        self.db.connect()
        query = """UPDATE BookCopy SET Status = 'Decommissioned' WHERE BookID = ?"""
        params = (bookID, )
        self.db.execute(query, params)
        self.db.commit()
        
        # Any active loans for that book are cancelled, and the notifyLoanCancelled method of notificationManager is called, to notify readers of this
        query2 = """SELECT LoanID, ReaderID FROM Loan WHERE BookID = ?"""
        self.db.execute(query2, params)
        loans = self.db.fetchAll()
        if loans:
            for loan in loans:
                query3 = """UPDATE Loan SET LoanStatus = 'Cancelled' WHERE LoanID = ? AND LoanEndDate > DATE('now')"""
                params3 = (loan[0], )
                self.db.execute(query3, params3)
                self.db.commit()
                self.notificationManager.notifyLoanCancelled(loan[0], loan[1], bookID)
        # Any reservations for that book are cancelled and the notifyReservationCancelled method of notificationManager is called to notify readers of this change       
        query4 = "SELECT ReservationID, ReaderID FROM Reservation WHERE BookID = ?"
        self.db.execute(query4, params)
        reservations = self.db.fetchAll()
        if reservations:
            for reservation in reservations:
                query5 = """UPDATE Reservation SET ReservationStatus = 'Cancelled' WHERE ReservationID = ?"""
                params5 = (reservation[0], )
                self.db.execute(query5, params5)
                self.db.commit()
                self.notificationManager.notifyReservationCancelled(reservation[0], reservation[1], bookID)
    
    # Method to retrieve all existing author names in the database to populate the choices attribute of the author name field of the AddBookForm, to allow the librarian to choose an existing author as the author of a new book 
    def getAuthorOptions(self):
        self.db.connect()
        query = """SELECT AuthorFirstName || ' ' || AuthorLastName FROM Author"""
        params = ()
        self.db.execute(query, params)
        authorNames = self.db.fetchAll()
        self.db.close()
        return authorNames
    
    # Method to retrieve all existing publisher names in the database to populate the choices attribute of the publisher name field of the AddBookForm, to allow the librarian to choose an existing author as the author of a new book 
    def getPublisherOptions(self):
        self.db.connect()
        query = """SELECT PublisherName FROM Publisher"""
        params = ()
        self.db.execute(query, params)
        publisherRows = self.db.fetchAll()
        self.db.close()
        publishers = []
        for publisher in publisherRows:
            publishers.append(publisher[0])
        return publishers
    
    # Method to add a new book to the library
    # Takes in parameters of title, genre ISBN13, year publisher, publisher and a list of bookAuthors which may contain more than one value if there are multiple author, the cover image link, the number of copies of the book being added to the library and the accession number of the aquisition
    def addBook(self, title, genre, isbn13, yearPublished, publisher, bookAuthors, blurb, minYearGroup, coverImageLink, numberOfCopies, accessionNumber):
        self.db.connect()
        # For each author in bookAuthors, the author's name is queried from the database and if the author already exists in the database their authorID is fetched, if not they are inserted as a new author in the database and their row ID is fetched
        authorIDs = []
        for author in bookAuthors:
            authorNames = author.split()
            authorFirstName = ' '.join(authorNames[:-1])
            authorLastName = authorNames[-1]
            
            query = """SELECT AuthorID FROM Author WHERE AuthorFirstName = ? and AuthorLastName = ?"""
            params = (authorFirstName, authorLastName)
            self.db.execute(query, params)
            existingAuthor = self.db.fetchOne()
            
            if existingAuthor:
                authorID = existingAuthor[0]
            else:
                query2 = """INSERT INTO Author (AuthorFirstName, AuthorLastName) VALUES (?, ?)"""
                self.db.execute(query2, params)
                authorID = self.db.getLastRowID()
                self.db.commit()
            
            authorIDs.append(authorID)
            
        # The publisher's name is queried and if it doesn't already exist in the database it is inserted and the row ID of that insertion is retrieved else the ID of the existing publisher record is returned
        query3 = """SELECT PublisherID FROM Publisher WHERE PublisherName = ?"""
        params3 = (publisher, )
        self.db.execute(query3, params3)
        existingPublisher = self.db.fetchOne()
        if existingPublisher:
            publisherID = existingPublisher[0]
        else:
            query4 = """INSERT INTO Publisher (PublisherName) VALUES (?)"""
            self.db.execute(query4, params)
            publisherID = self.db.getLastRowID()
            self.db.commit()
        
        # Inserts the book information into the book table
        dateAdded = date.today()
        query5 = """INSERT INTO Book (ISBN, Title, Genre, YearPublished, PublisherID, DateAdded, Blurb, MinYearGroup, CoverImageURL) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        params5 = (isbn13, title, genre, yearPublished, publisherID, dateAdded, blurb, minYearGroup, coverImageLink)
        self.db.execute(query5, params5)
        bookID = self.db.getLastRowID()
        self.db.commit()
        
        # Inserts the author information into the AuthorBook linking table
        for id in authorIDs:
            query6 = """INSERT INTO AuthorBook (AuthorID, BookID) VALUES (?, ?)"""
            params6 = (id, bookID)
            self.db.execute(query6, params6)
            self.db.commit()
        
        # Inserts a copy into the BookCopy table for that book for the number of copies added to the library
        for i in range(numberOfCopies):
            query7 = """INSERT INTO BookCopy (CopyID, BookID, AccessionNumber, Status) VALUES (?, ?, ?, ?)"""
            params7 = (i+1, bookID, accessionNumber, 'Available')
            self.db.execute(query7, params7)
            self.db.commit()
        
        self.db.close()
        return flash(f"You have successfully added {numberOfCopies} copies of {title} to the library.")       

# Defines a Loan class 
class Loan():
    
    # Constructor for the Book class
    # Takes the filename of the SQLite database file as a parameter
    # Takes an instance of the NotificationManager class as a parameter
    def __init__(self, notificationManager, dbName):
        self.notificationManager = notificationManager
        self.db = Database(dbName)
    
    # Method to allow the reader to loan a book
    def loanBook(self, readerID, bookID, bookTitle):
        self.db.connect()
        # Retrieves the yeaar group of the reader
        query = "SELECT YearGroup FROM Reader WHERE ReaderID = ?"
        params = (readerID, )
        self.db.execute(query, params)
        yeargroup = self.db.fetchOne()[0]
        
        # Retrieves the minimum year group of that is allowed to read the book
        query2 = "SELECT MinYearGroup FROM Book WHERE Book.BookID = ?"
        params2 = (bookID, )
        self.db.execute(query2, params2)
        minyeargroup = self.db.fetchOne()[0]
        
        # Checks is the reader is old enough the read the book, if not displys a message on the screen
        if (yeargroup < minyeargroup) and (yeargroup not in [0, 1]):
            return flash("You are not old enough to loan this book.")
        else:
            # Sets the allowance of books a reader is allowed to have out at any given time dependent on their year group, if that are in year 12 or 13 or are a staff member or librarian they have a bigger allowance
            if (yeargroup in [0, 1, 12, 13]):
                allowance = 5
            else:
                allowance = 3
            
            # Retrieves the number of active loans the reader has
            query3 = """SELECT COUNT(*) FROM Loan WHERE Loan.ReaderID = ? AND Loan.LoanStatus = 'Active'"""
            params3 = (readerID, )
            self.db.execute(query3, params3)
            activeLoans = self.db.fetchOne()[0]
            
            # If the number of active loans equals or exceeds their allowance a message is displayed telling them they are not allowed to loan the book
            if activeLoans >= allowance:
                return flash(f"You have reached the limit of {activeLoans} active loans.")
            else: 
                # If they are within their allowance, they are allowed to loan the book
                # Retrieves an available book copy id for that book - there is always one available if this method has run
                query4 = """SELECT BookCopy.CopyID FROM BookCopy WHERE BookCopy.BookID = ? AND BookCopy.Status = 'Available'"""
                params4 = (bookID, )
                self.db.execute(query4, params4)
                copyID = self.db.fetchOne()[0]
                
                # Sets the start date of the loan to today's date and sets the end date as 2 weeks from today's date
                dateNow = date.today()
                dateTwoWeeks = date.today() + datetime.timedelta(14)
                query5 = """INSERT INTO Loan (CopyID, BookID, ReaderID, LoanStartDate, LoanEndDate, LoanStatus) VALUES (?, ?, ?, ?, ?, ?)"""
                params5 = (copyID, bookID, readerID, dateNow, dateTwoWeeks, 'Active') 
                self.db.execute(query5, params5)
                self.db.commit()
                
                # Updates the status of the book copy to 'On Loan'
                query6 = """UPDATE BookCopy SET Status = 'On Loan' WHERE CopyID = ? AND BookID = ?"""
                params6 = (copyID, bookID)
                self.db.execute(query6, params6)
                self.db.commit()
                
                # Method to display the due date to the reader in a clear format e.g. Book due on 9th May 2024
                def addSuffix(myDate):
                    date_suffix = ["th", "st", "nd", "rd"]

                    if myDate % 10 in [1, 2, 3] and myDate not in [11, 12, 13]:
                        return date_suffix[myDate % 10]
                    else:
                        return date_suffix[0]
                suffix = addSuffix(int(dateTwoWeeks.strftime("%d").lstrip("0").replace(" 0", " ")))
                dueDate = dateTwoWeeks.strftime("%d").lstrip("0").replace(" 0", " ") + suffix + " " + dateTwoWeeks.strftime("%B %Y")
                username = session['username']
                return flash(f"Hi {username}. You have successfully loaned {bookTitle}! It is due back on {dueDate}")
    
    # Method to retrieve all the loans for a reader
    # Dual purpose, if readerID is not provided it will retrieve all the loans of the reader currently using the system
    # If a readerID is provided, it will retrieve the loans for that specific reader for the librarian
    def getLoans(self, readerID=None):
        self.db.connect()
        query = """SELECT Loan.LoanID, Loan.CopyID, Loan.BookID, Loan.LoanStartDate, Loan.LoanEndDate, Book.CoverImageURL FROM Loan INNER JOIN Book On Loan.BookID = Book.BookID WHERE Loan.ReaderID = ? AND Loan.LoanStatus = 'Active' ORDER BY Loan.LoanStartDate DESC"""
        if readerID is not None:
            params = (readerID, )
        else:
            params = (session['readerID'], )
        self.db.execute(query, params)
        loans = self.db.fetchAll()
        return loans
    
    # Method to return a loan, called when the reader presses return button on loan
    def returnLoan(self, loanID, copyID, bookID):
        self.db.connect()
        # Updates loan status to 'Ended'
        query = """UPDATE Loan Set LoanStatus = ? WHERE LoanID = ?"""
        params = ('Ended', loanID)
        self.db.execute(query, params)
        self.db.commit()
        # Updates BookCopy status to 'Available'
        query2 = """UPDATE BookCopy SET Status = ? WHERE CopyID = ? AND BookID = ?"""
        params2 = ('Available', copyID, bookID)
        self.db.execute(query2, params2)
        self.db.commit()
        
        # Checks if there are any reservations for the book that just became available, an retrieves the reservation whose queue position is 1
        query3 = """SELECT ReservationID FROM Reservation WHERE CopyID = ? AND BookID = ? ORDER BY QueuePosition ASC"""
        params3 = (copyID, bookID)
        self.db.execute(query3, params3)
        reservationID = self.db.fetchOne()
        
        # If there is a reservation for the book, that reservation's status is changed from 'Pending' to 'Fulfilled' and the readerID of the reader who made that reservation is returned
        if reservationID:
            query4 = """UPDATE Reservation SET ReservationStatus = 'Fulfilled' WHERE ReservationID = ? RETURNING ReaderID"""
            params4 = (reservationID[0], )
            self.db.execute(query4, params4)
            readerID = self.db.fetchOne()[0]
            self.db.commit()
            
            # A new loan is inserted into the table for the book that just became available that the reservation is for, with status 'Active'
            dateNow = date.today()
            dateTwoWeeks = date.today() + datetime.timedelta(14)
            query5 = """INSERT INTO Loan (CopyID, BookID, ReaderID, LoanStartDate, LoanEndDate, LoanStatus) VALUES (?, ?, ?, ?, ?, ?)"""
            params5 = (copyID, bookID, readerID, dateNow, dateTwoWeeks, 'Active')
            self.db.execute(query5, params5)
            self.db.commit()
            params6 = ('On Loan', copyID, bookID)
            self.db.execute(query2, params6)
            self.db.commit()
            # The notifyReservationAvailable method of the notificationManager object is called which inserts a notification into the Notification table for that reader to alert them that their reservation is available
            self.notificationManager.notifyReservationAvailable(reservationID[0], bookID, readerID)

        # The book title of the loan just returned by the reader is returned to be formatted into a message for them
        query5 = "SELECT Title FROM Book WHERE BookID = ?"
        params7 = (bookID, )
        self.db.execute(query5, params7)
        title = self.db.fetchOne()[0]
        return title

# Defines a NotificationManager class
class NotificationManager():
    
    # Takes the filename of the SQLite database file as a parameter
    def __init__(self, dbName):
        self.db = Database(dbName)
        
    # Notifications will work as follows: when certain actions occur methods of this class will be triggered which will insert notifications for readers into the Notification table as Unread
    # When the reader next logs on or if they are currently logged in they will see a notificiation icon signifying they have unread notifications and once they have viewed them they will not be able to see them again
    
    # Method to notify when a reservation is available
    def notifyReservationAvailable(self, reservationID, bookID, readerID):
        self.db.connect()
        # Insert into notification the type of notification 'reservation', the intended readerID of the notifications and the reservationID and bookID
        query = """INSERT INTO Notification (NotificationType, Viewed, ReaderID, BookID, ReservationID) VALUES (?, ?, ?, ?, ?)"""
        params = ('Reservation', 0, readerID, bookID, reservationID)
        self.db.execute(query, params)
        self.db.commit()
        self.db.close()
    
    # Method to notify a reader when a loan needs to be returned 1 day before
    def notifyLoanToReturn(self, readerID):
        self.db.connect()
        # Retrieves all active loans for that reader whose end date is 1 day after the current date
        query = """SELECT Loan.BookID, Loan.ReaderID, Loan.LoanID FROM Loan WHERE Loan.ReaderID = ? AND Loan.LoanStatus = 'Active' AND Loan.LoanEndDate = DATE('now', '+1 day')"""
        params = (readerID, )
        self.db.execute(query, params)
        loansToReturn = self.db.fetchAll()
        # For each retrieved loan, a notification fo type 'Return Loan' is inserted into Notification
        for loan in loansToReturn:
            query2 = """INSERT INTO Notification (NotificationType, Viewed, ReaderID, BookID, LoanID) VALUES (?, ?, ?, ?, ?)"""
            params2 = ('Return Loan', 0, loan[1], loan[0], loan[2])
            self.db.execute(query2, params2)
            self.db.commit()
        self.db.close()
    
    # Method to notify a reader their loan has been cancelled
    def notifyLoanCancelled(self, loanID, readerID, bookID):
        self.db.connect()
        # A notification of type 'Cancelled Loan' is inserted into Notification
        query = """INSERT INTO Notification (NotificationType, Viewed, ReaderID, BookID, LoanID) VALUES (?, ?, ?, ?, ?)"""
        params = ('Cancelled Loan', 0, readerID, bookID, loanID)
        self.db.execute(query, params)
        self.db.commit()
        self.db.close()
    
    # Method to notify a reader that their reservation has been cancelled
    def notifyReservationCancelled(self, reservationID, readerID, bookID):
        self.db.connect()
        # A notification of type 'Cancelled Reservation' is inserted into Notification
        query = """INSERT INTO Notification (NotificationType, Viewed, ReaderID, BookID, ReservationID) VALUES (?, ?, ?, ?, ?)"""
        params = ('Cancelled Reservation', 0, readerID, bookID, reservationID)
        self.db.execute(query, params)
        self.db.commit()
        self.db.close()
    
    # A method to send overdue notifications to the reader periodically 
    def overdueLoan(self, readerID):
        self.db.connect()
        # Gets today's date and calculates dates 1, 5, 10, 15 and 20 days before this date
        today = date.today()
        dueDates = [today - datetime.timedelta(days=days) for days in [1, 5, 10, 15, 20]]
        # Retrieves all loans for that reader with an 'Active' status whose are overdue by 1, 5, 10, 15 or 20 days
        query = """SELECT Loan.BookID, Loan.ReaderID, Loan.LoanID FROM Loan WHERE ReaderID = ? AND LoanStatus = 'Active' AND LoanEndDate IN (?, ?, ?, ?, ?)"""
        params = (readerID, *dueDates)
        self.db.execute(query, params)
        overdueLoans = self.db.fetchAll()
        # For each overdue loan a notification is inserted into Notification of type 'Overdue Loan'
        for loan in overdueLoans:
            query2 = """INSERT INTO Notification (NotificationType, Viewed, ReaderID, BookID, LoanID) VALUES (?, ?, ?, ?, ?)"""
            params2 = ('Overdue Loan', 0, loan[1], loan[0], loan[2])
            self.db.execute(query2, params2)
            self.db.commit()
        self.db.close()
    
    # A method to retrieve all unread notifications for a reader   
    def getNotificationsForReader(self, readerID):
        self.db.connect()
        # Retrieves unread notifications and associated information for each notfication, e.g. the book title of the overdue loan
        query = """SELECT Notification.NotificationID, Notification.NotificationType, Notification.BookID, Notification.ReservationID, Notification.LoanID, Book.Title, Loan.LoanEndDate, Book.CoverImageURL FROM Notification INNER JOIN Book ON Notification.BookID = Book.BookID LEFT JOIN Loan ON Notification.LoanID = Loan.LoanID WHERE Notification.ReaderID = ? AND Notification.Viewed = 0"""
        params = (readerID, )
        self.db.execute(query, params)
        notifications = self.db.fetchAll()
        self.db.close()
        # Copies the NotificationID of each notification into a new list 
        notificationIDs = []
        for notification in notifications:
            notificationIDs.append(notification[0])
        self.db.close()
        return notifications, notificationIDs

    # Method to mark notifications as viewed once they have been seen by the reader so that the reader only sees unread notifications
    def markNotificationsAsViewed(self, notificationIDs):
        self.db.connect()
        # For each notificationID the associated record's viewed field in the Notification table is updates to 1 signifying 'Read'
        for id in notificationIDs:
            query = """UPDATE Notification SET Viewed = 1 WHERE NotificationID = ?"""
            params = (id, )
            self.db.execute(query, params)
            self.db.commit()
        self.db.close()

# Defines a Queue data structure
class Queue(): 
    
    # Constructor of Queue class
    # Initialises list to act as queue
    def __init__(self):
        self.queue = []
        
    # Method to add items to end of queue
    def enqueue(self, item):
        self.queue.append(item)

    # Method to retrieve items from front of queue if the queue is not empty, else returns None instead of the item
    def dequeue(self):
        if self.isEmpty():
            return None
        return self.queue.pop(0)

    # Method to check if queue is empty by returning the True or False based on what the condition evaluates to
    def isEmpty(self):
        return len(self.queue) == 0

    # Method to get the number of items in the queue
    def getSize(self):
        return len(self.queue)
    
    # Method to clear the queue of items
    def clear(self):
        self.queue = []        

# Defines a Priority Queue data structure that inherits behaviour from Queue
class PriorityQueue(Queue):
    
    # Constructor of PriorityQueue class calls Queue constructor
    def __init__(self):
        super().__init__()

    # Method that overrides enqueue method in Queue class
    # Appends reservations to a queue and custom sorts them based on their queue position and then their priority
    def enqueue(self, reservationID, queuePosition, priority):
        self.queue.append([reservationID, queuePosition, priority])
        self.queue = sorted(self.queue, key=lambda x: (x[1], x[2]))

    # Method to override the dequeue method in the Queue class
    # Removes an item from the back of the list for processing if the Queue is not empty
    # Order items dequeued does not matter in this implementation
    def dequeue(self):
        if self.isEmpty():
            return None
        return self.queue.pop() 

# Defines a Reservation class
class Reservation():

    # Constructor for the Reservation class
    # Takes the filename of the SQLite database file as a parameter
    # Initialises an instance of PriorityQueue()
    def __init__(self, dbName):
        self.db = Database(dbName)
        self.reservationQueue = PriorityQueue()
    
    # Method to allow a reader to reserve a book
    def reserveBook(self, readerID, bookID):
        self.db.connect()
        # Retrieves the copyID for the specified book that has the least number of reservations
        query = """SELECT IFNULL(
        (SELECT Reservation.CopyID FROM Reservation WHERE Reservation.BookID = ? GROUP BY CopyID ORDER BY COUNT(*) ASC LIMIT 1), 1) AS CopyID"""
        params = (bookID, )
        self.db.execute(query, params)
        copyID = self.db.fetchOne()[0]
        
        # Calls the getReservationsForQueue method to populate the reservationQueue with the existing reservations for that book
        self.getReservationsForQueue(bookID, copyID)
        
        # Retrieves the priority of the readerID making the reservation - if they are not in year 12 or 13 or staff or a librarian then they are priority 2 else 1
        query2 = """SELECT CASE WHEN YearGroup BETWEEN 2 AND 10 THEN 2 ELSE 1 END AS Priority FROM Reader WHERE ReaderID = ?"""
        params2 = (readerID, )
        self.db.execute(query2, params2)
        priority = self.db.fetchOne()[0]
        # Calls the findNewReservationPositions method to retrieve the new queue positions of all the reservations now that a new reservation has been made
        self.findNewReservationPositions(priority)
        status = 'Pending'
        # Calls the updateReservationsTable method to insert the new reservation into the database and update the queue positions of the existing reservations in the database
        self.updateReservationsTable(bookID, copyID, readerID, status, priority)
        # Empty the reservationQueue for the next method call
        self.reservationQueue.clear()
    
    # Method to populate the reservationQueue with the existing reservations for that book
    def getReservationsForQueue(self, bookID, copyID):
        self.db.connect()
        # Retrieve all reservations for specified book
        query = """SELECT ReservationID, QueuePosition, Priority FROM Reservation WHERE Reservation.BookID = ? AND Reservation.CopyID = ? AND Reservation.ReservationStatus = 'Pending' ORDER BY Reservation.QueuePosition ASC"""
        params = (bookID, copyID)
        self.db.execute(query, params)
        reservations = self.db.fetchAll()
        # Enqueue each reservation to queue
        for reservation in reservations:
            self.reservationQueue.enqueue(reservation[0], reservation[1], reservation[2])

    # Method to retrieve the new queue positions of all the reservations now that a new reservation has been made
    def findNewReservationPositions(self, newReservationPriority):
        queueLength = self.reservationQueue.getSize()
        i = 0
        # While the queue is not empty and the current reservation has a lower priority than new reservation increment i
        while i < queueLength and self.reservationQueue.queue[i][2] <= newReservationPriority:
            i += 1
        # Insert new reservation into queue
        self.reservationQueue.queue.insert(i, [None, i+1, newReservationPriority])
        # Update queue positions for all reservations
        for idx, reservation in enumerate(self.reservationQueue.queue):
            reservation[1] = idx+1

    # Method to insert the new reservation into the database and update the queue positions of the existing reservations in the database
    def updateReservationsTable(self, bookID, copyID, readerID, status, priority):
        self.db.connect()
        # Dequeue each reservation
        while not self.reservationQueue.isEmpty():
            reservation = self.reservationQueue.dequeue()
            # If reservation is the new reservation insert new record into Reservation table
            if reservation[0] == None:
                query = """INSERT INTO Reservation (CopyID, BookID, ReaderID, ReservationStatus, QueuePosition, Priority) VALUES (?, ?, ?, ?, ?, ?)"""
                params = (copyID, bookID, readerID, status, reservation[1], priority)
                self.db.execute(query, params)
                self.db.commit()
            else:
            # If existing reservation update its queue position
                query = """UPDATE Reservation SET QueuePosition = ? WHERE ReservationID = ?"""
                params = (reservation[1], reservation[0])
                self.db.execute(query, params)
                self.db.commit()
                
        self.db.close()
    
    # Method to get all the pending reservations for a reader
    # Dual purpose - if no readerID is provided then retrieves the pending reservations for the current reader
    # If readerID provided then retrieves that reader's pending reservations for the librarian
    def getReservations(self, readerID=None):
        self.db.connect()
        query = """SELECT Book.Title, Reservation.BookID, Reservation.ReservationStatus, Reservation.ReservationTimestamp, Reservation.QueuePosition, Reservation.ReservationID, Book.CoverImageURL FROM Reservation INNER JOIN Book ON Reservation.BookID = Book.BookID WHERE Reservation.ReservationStatus = 'Pending' AND Reservation.ReaderID = ?"""
        if readerID is not None:
            params = (readerID, )
        else:
            params = (session['readerID'], )
        self.db.execute(query, params)
        reservations = self.db.fetchAll()
        self.db.close()
        return reservations
    
    # Method to cancel a reservation
    def cancelReservation(self, bookID, reservationID):
        self.db.connect()
        # Updates reservation status to Fulfilled
        query = """UPDATE Reservation SET ReservationStatus = 'Fulfilled' WHERE ReservationID = ?"""
        params = (reservationID, )
        self.db.execute(query, params)
        self.db.commit()
        # Returns the title of the book the reservation for so that it can be returned in a message to the reader
        query2 = """SELECT Title FROM Book WHERE BookID = ?"""
        params2 = (bookID, )
        self.db.execute(query2, params2 )
        title = self.db.fetchOne()[0]
        return title

# Defines a PDFManagement class that contains methods to allow for creation, edit
class PDFManagement():
    
    # Constructor for PDF Management class
    # Initialises a buffer object to store a stream of bytes that can be treated like a file-object
    # This buffer will be where report data for the PDF is stored
    def __init__(self):
        self.buffer = BytesIO()
    
    # Method to create a canvas object so that any operations on Canvas will output to the buffer
    # Defining the page size of the document as letter
    def createCanvas(self):
        self.c = canvas.Canvas(self.buffer, pagesize=letter)
    
    # Sets font of text as Helvetica and size 12 and writes text data at specified coordinates
    def write(self, x, y, data):
        self.c.setFont("Helvetica", 12)
        self.c.drawString(x, y, data)
    
    # Creates a new page on the canvas and adds a title at the specified coordinates on that page
    def addPage(self, title):
        self.c.showPage()
        self.c.setFont("Helvetica", 12)
        self.c.drawString(25, 750, title)
    
    # Method to save the changes to the canvas
    def save(self):
        self.c.save()
    
    # Returns the bytes content of the buffer
    def getContent(self):
        return self.buffer.getvalue()
    
    # Method to draw a table on the canvas with provided data
    def drawTable(self, data, startX, startY, rowHeight, columnWidth):
        for i, row in enumerate(data):
            for j, cell in enumerate(row):
                # Calculate coordinates to start writing at for each cell
                x = startX + j * columnWidth
                y = startY - i * rowHeight
                # Convert cell data to string and write it at the specified coordinates
                cell_text = str(cell)
                self.write(x, y, cell_text)

# Defines a Report class
class Report():
    
    # Constructor for the Report class
    # Takes the filename of the SQLite database file as a parameter
    # Initialises an instance of the PDFManagement class to interact with to create report PDFs
    def __init__(self, dbName):
        self.db = Database(dbName)
        self.pdfManager = PDFManagement()
    
    # Method to create a Top Readers in X Genre in Y Time period Report
    def getTopReadersGenreTime(self, numberOfReaders, genre, startDate, endDate):
        # Write the title of the report at top of PDF canvas
        title = f"Top {numberOfReaders} Readers in {genre} between {startDate} and {endDate}"
        self.pdfManager.createCanvas()
        self.pdfManager.write(100, 750, title)
        self.db.connect()
        # Retrieve the readers who have read the most books in the specified genre between the specified time period
        query = """SELECT Reader.FirstName || ' ' || Reader.LastName AS FullName, CASE 
          WHEN Reader.YearGroup = 0 THEN 'Staff'
          WHEN Reader.YearGroup = 1 THEN 'Librarian'
          ELSE 'Year ' || CAST(Reader.YearGroup AS TEXT)
      END AS YearGroupLabel, COUNT(Loan.ReaderID) AS LoanCount FROM Reader INNER JOIN Loan ON Reader.ReaderID = Loan.ReaderID INNER JOIN Book ON Loan.BookID = Book.BookID WHERE Book.Genre LIKE '%' || ? || '%' AND LoanStartDate BETWEEN ? AND ? GROUP BY Reader.ReaderID ORDER BY LoanCount DESC"""
        params = (genre, startDate, endDate)
        self.db.execute(query, params)
        # Retrieve the reader name, year grou and number of loans for the number of readers specified
        results = self.db.fetchMany(numberOfReaders)
        # If there are no results write message to PDF and save changes
        if not results:
            self.pdfManager.write(100, 700, "No results.")
            self.pdfManager.save()
        # If there are results write the results into a table on the PDF and save changes
        else:
            results.insert(0, ("Name", "Year Group", "Number of Books Read"))
            self.pdfManager.drawTable(results, 100, 730, 20, 100)
            self.pdfManager.save()
        
        # Get the bytes content of the pdf
        pdfContent = self.pdfManager.getContent()
        # Insert a new report into the Report table with the title and content of the report
        query2 = """INSERT INTO Report (ReportTitle, PDFContent) VALUES (?, ?)"""
        params2 = (title, pdfContent)
        self.db.execute(query2, params2)
        # Return the reportID so that it can be used to retrieve a report
        reportID = self.db.getLastRowID()
        self.db.commit()
        self.db.close()
        return reportID

    # Method to create a Top Readers in X Year Group in Y Time Period
    def getTopReadersYearGroup(self, numberOfReaders, yearGroup, startDate, endDate):
        # Write the title of the report at top of the page
        title = f"Top {numberOfReaders} Readers in Year {yearGroup} between {startDate} and {endDate}"
        self.pdfManager.createCanvas()
        self.pdfManager.write(100, 750, title)
        self.db.connect()
        # Retrieve the readers who have read the most books in the specified year group during the specified time period by checking the start date of their loans
        query = """SELECT Reader.FirstName || ' ' || Reader.LastName AS FullName, COUNT(Loan.ReaderID) AS LoanCount FROM Reader INNER JOIN Loan ON Reader.ReaderID = Loan.ReaderID WHERE Reader.YearGroup = ? AND LoanStartDate BETWEEN ? AND ? GROUP BY Reader.ReaderID ORDER BY LoanCount DESC"""
        params = (int(yearGroup), startDate, endDate)
        self.db.execute(query, params)
        # Retrieve the name, and number of loans read by each reader for the number of readers specified
        results = self.db.fetchMany(numberOfReaders)
        # If there are no results write this message to the PDF and save changes
        if not results:
            self.pdfManager.write(100, 700, "No results.")
            self.pdfManager.save()
        # If there are results write the results into a table in the PDF and save changes
        else:
            results.insert(0, ("Name", "Number of Books Read"))  
            self.pdfManager.drawTable(results, 100, 730, 20, 100)
            self.pdfManager.save()
        
        # Get the bytes content of canvas for PDF
        pdfContent = self.pdfManager.getContent()
        # Insert the title and content as a new report record in the Report table
        query2 = """INSERT INTO Report (ReportTitle, PDFContent) VALUES (?, ?)"""
        params2 = (title, pdfContent)
        self.db.execute(query2, params2)
        # Return the new report ID
        reportID = self.db.getLastRowID()
        self.db.commit()
        self.db.close()
        return reportID
    
    # Method to generate a report for every reader who has overdue loans
    # Each new reader's report will be on a new page, so the librarian can print the report and send each report to each individual
    def getOverdueLoanReports(self, days):
        self.db.connect()
        # Set the overdue date as the today's date subtracted by the number of days overdue
        today = date.today()
        overduedate = today - datetime.timedelta(days=days)
        # Retrieve all loans that are overdue by the specified number of days
        query = """SELECT Reader.FirstName || ' ' || Reader.LastName AS FullName, CASE 
          WHEN Reader.YearGroup = 0 THEN 'Staff'
          WHEN Reader.YearGroup = 1 THEN 'Librarian'
          ELSE 'Year ' || CAST(Reader.YearGroup AS TEXT)
      END AS YearGroupLabel, Reader.Houseroom, Loan.LoanStartDate, Loan.LoanEndDate, Book.Title FROM Reader INNER JOIN Loan ON Reader.ReaderID = Loan.ReaderID INNER JOIN Book ON Loan.BookID = Book.BookID WHERE Loan.LoanStatus = 'Active' AND Loan.LoanEndDate = ?"""
        params = (overduedate, )
        self.db.execute(query, params)
        # Retrieve the reader's name, year group, houseroom and loan details for each overdue loan
        results = self.db.fetchAll()
        # Organise the results into a dicitonary, where the reader's name is the key and the value is a list of lists containing information about each of their overdue loans
        organisedResults = {}
        for row in results:
            name = row[0]
            yeargroup = row[1]
            houseroom = row[2]
            loanstartdate = row[3]
            loanenddate = row[4]
            booktitle = row[5]
            if name not in organisedResults:
                organisedResults[name] = []
            organisedResults[name].append([yeargroup, houseroom, loanstartdate, loanenddate, booktitle])
        self.pdfManager.createCanvas()
        # For each reader add a new page to the report and write their overdue loans onto it
        for key, value in organisedResults.items():
            self.pdfManager.addPage(f"Overdue Loan Notice for {key} {value[0][0]} {value[0][1]}")
            for i, loan in enumerate(value):
                self.pdfManager.write(25, 730 - (i*50), f"Their Loan for {loan[4]} made on the {loan[2]} and due on the {loan[3]} is {days} days overdue.")
                
            self.pdfManager.write(25, 200, "Please hand in the overdue books to the library as soon as possible.")
            
        # Save changes to canvas
        self.pdfManager.save()
        # Get bytes content of PDF   
        pdfContent = self.pdfManager.getContent()
        # Insert title and pdf content as new report in Report table
        query2 = """INSERT INTO Report (ReportTitle, PDFContent) VALUES (?, ?)"""
        today = date.today()
        params2 = (f"Overdue Loans Report For {today}", pdfContent)
        self.db.execute(query2, params2)
        # Return reportID of new report
        reportID = self.db.getLastRowID()
        self.db.commit()
        self.db.close()
        return reportID

    # Method to retrieve the bytes content of an existing report
    def getExistingReport(self, reportID):
        self.db.connect()
        query = """SELECT PDFContent FROM Report WHERE ReportID = ?"""
        params = (reportID, )
        self.db.execute(query, params)
        reportData = self.db.fetchOne()[0]
        self.db.close()
        return reportData
    
    # Method to retrieve the reportID of an existing report
    def getExistingReportByTitle(self, title):
        self.db.connect()
        query = """SELECT ReportID FROM Report WHERE ReportTitle = ?"""
        params = (title, )
        self.db.execute(query, params)
        reportID = self.db.fetchOne()[0]
        self.db.close()
        return reportID
    
    # Method to get the titles of all previously created reports to fill the choices attribute of a field in the Report Form so that the librarian can choose a past report to view/download/print
    def getAllPastReportTitles(self):
        self.db.connect()
        query = "SELECT ReportID, ReportTitle FROM Report"
        params = ()
        self.db.execute(query, params)
        reportTitles = self.db.fetchAll()
        return reportTitles

# Initialise classes
reader = Reader(DBNAME) 
userManagement = UserManagement(reader, DBNAME)
readingList = ReadingList(DBNAME)
review = Review(DBNAME)
notificationManager = NotificationManager(DBNAME)
book = Book(notificationManager, DBNAME)
loan = Loan(notificationManager, DBNAME)
reservation = Reservation(DBNAME)
report = Report(DBNAME)

# Defines a FlaskForm Class called RegistrationForm that will allow a user to input their details and register a new account
class RegistrationForm(FlaskForm):
    readerFirstName = StringField("First Name:", validators=[DataRequired(), Length(min=1, max=15)])
    readerLastName = StringField("Last Name:", validators=[DataRequired(), Length(min=1, max=15)])
    readerUsername = StringField("Enter a Username:", validators=[DataRequired(), Length(min=1, max=15)])
    readerPassword = PasswordField("Password:", validators=[DataRequired(), Length(min=4, max=15), userManagement.passwordValidator])
    confirmPassword = PasswordField('Confirm Password:', validators=[DataRequired(), EqualTo('readerPassword', message='Passwords must match')])
    readerSchoolEmailAddress = StringField("School Email Address:", validators=[DataRequired(), Length(min=1, max=25), userManagement.schoolEmailValidator])
    readerPersonalEmailAddress = StringField("Personal Email Address:", validators=[DataRequired(), Length(min=1, max=25), userManagement.personalEmailValidator])
    readerDateOfBirth = DateField("Date of Birth YYYY-MM-DD:", format="%Y-%m-%d", validators=[DataRequired()])
    readerYearGroup = SelectField("Year Group:", choices=[("7", "2nd Form"), ("8", "3rd Form"), ("9", "Lower 4th"), ("10", "Upper 4th"), ("11", "5th Form"), ("12", "Lower 6th"), ("13", "Upper 6th"), ("0", "Staff"), ("1", "Librarian")])
    readerHouseroom = SelectField("Houseroom:", choices=[('Le1a', 'Le1a'), ('Le1b', 'Le1b'), ('Le2', 'Le2'), ('Le3', 'Le3'), ('Le4', 'Le4'), ('Le5', 'Le5'), ('Le6', 'Le6'), ('Le7', 'Le7'),  ('Wa1a', 'Wa1a'), ('Wa1b', 'Wa1b'), ('Wa2', 'Wa2'), ('Wa3', 'Wa3'), ('Wa4', 'Wa4'), ('Wa5', 'Wa5'), ('Wa6', 'Wa6'), ('Wa7', 'Wa7'),  ('Ca1a', 'Ca1a'), ('Ca1b', 'Ca1b'), ('Ca2', 'Ca2'), ('Ca3', 'Ca3'), ('Ca4', 'Ca4'), ('Ca5', 'Ca5'), ('Ca6', 'Ca6'), ('Ca7', 'Ca7'),  ('Ch1a', 'Ch1a'), ('Ch1b', 'Ch1b'), ('Ch2', 'Ch2'), ('Ch3', 'Ch3'), ('Ch4', 'Ch4'), ('Ch5', 'Ch5'), ('Ch6', 'Ch6'), ('Ch7', 'Ch7'),  ('Ma1a', 'Ma1a'), ('Ma1b', 'Ma1b'), ('Ma2', 'Ma2'), ('Ma3', 'Ma3'), ('Ma4', 'Ma4'), ('Ma5', 'Ma5'), ('Ma6', 'Ma6'), ('Ma7', 'Ma7'),  ('Wi1a', 'Wi1a'), ('Wi1b', 'Wi1b'), ('Wi2', 'Wi2'), ('Wi3', 'Wi3'), ('Wi4', 'Wi4'), ('Wi5', 'Wi5'), ('Wi6', 'Wi6'), ('Wi7', 'Wi7'), ('Leicester', 'Leicester'), ('Walker', 'Walker'), ('Maltby', 'Maltby'), ('Wilkinson', 'Wilkinson'), ('Callender', 'Callender'), ('Chavasse', 'Chavasse')])
    readerAdminCode = StringField("Librarian admin code:")
    submit = SubmitField("Register")

# Defines a FlaskForm class called LoginForm to allow user to enter in the credentials for their account to log in to the system  
class LoginForm(FlaskForm):
    enteredUsername = StringField("Enter your username:", validators=[DataRequired(), Length(min=1, max=15)])
    enteredPassword = PasswordField("Enter your password:", validators=[DataRequired(), Length(min=1, max=15)])
    enteredAdminCode = StringField("Admin code:")
    submit = SubmitField("Login")

# Defines a FlaskForm class called EnterEmailForm to allow a user the enter in their school email and personal email to submit a request to chaneg their password, if they have forgtten it, if these emails exist in the system
class EnterEmailForm(FlaskForm):
    enteredSchoolEmail = StringField("School Email Address:", validators=[DataRequired(), Length(min=1, max=25)])
    enteredPersonalEmail = StringField("Personal Email Address:", validators=[DataRequired(), Length(min=1, max=25)]) 
    submit = SubmitField("Change Password")

# Defines a FlaskForm class called ChangePasswordForm to allow a reader to change their password by entering their username and then their new password
class ChangePasswordForm(FlaskForm):
    username = StringField("Enter your Username:", validators=[DataRequired(), Length(min=1, max=15)])
    newPassword = PasswordField("Enter a new password:", validators=[DataRequired(), Length(min=1, max=15), userManagement.passwordValidator])
    confirmPassword = PasswordField('Confirm new password:', validators=[DataRequired(), EqualTo('newPassword', message='Passwords must match')])
    submit = SubmitField("Change Password")

# Defines a FlaskForm class called SearchForm to allow a reader to search the library for books either by filling in the searchString field or by searching specific fields, such as searching by author first name, and to order their results
class SearchForm(FlaskForm):
    authorFirstName = StringField("Author First Name:")
    authorLastName = StringField("Author Last Name:")
    bookTitle = StringField("Book Title:")
    bookISBN = StringField("Book ISBN-13:")
    bookGenre = StringField("Genre:")
    searchString = StringField()
    orderByField = SelectField(choices=[("AuthorFirstName", "Author First Name"), ("AuthorLastName", "Author Last Name"), ("Title", "Book Title"), ("ISBN", "ISBN")])
    orderByDirection = SelectField(choices=[("ASC", "Ascending"), ("DESC", "Descending")])
    search = SubmitField("Search")

# Defines a FlaskForm class called ReaderSearchForm that allows a librarian to search the database for a reader
class ReaderSearchForm(FlaskForm):
    readerName = StringField("Enter reader's name:", validators=[DataRequired()])
    search = SubmitField("Search Accounts")

# Defines a FlaskForm class called ReviewForm that allows a reader to leave a review and a rating. The rating functionality is implemented in the HTML template and is sent through the request object
class ReviewForm(FlaskForm):
    reviewText = TextAreaField("Review", validators=[DataRequired(), Length(min=1, max=1000)])
    leaveReview = SubmitField("Leave Review")

# Defines a FlaskForm class called ReadingListForm to allow a reader to add a book to either an existing reading list or a new reading list
class ReadingListForm(FlaskForm):
    readingList = SelectField("Your Reading Lists:", choices=[], validators=[Optional()])
    newList = StringField("Create A New Reading List:")
    readOrNot = RadioField("Read?", choices=[("1", "Already Read"), ("0", "Want To Read")])
    addToList = SubmitField("Add to Reading List")

# Defines a FlaskForm class called ChangeEmailForm that allows a reader the change the personal email address associated with their account and school email address if it has changed
class ChangeEmailForm(FlaskForm):
    schoolEmail = StringField("School Email Address:", validators=[DataRequired(), Length(min=1, max=25)])
    personalEmail = StringField("Enter your new Personal Email Address:", validators=[DataRequired(), Length(min=1, max=25)])
    submit = SubmitField("Change Personal Email")

# Defines a FlaskForm class called AddBookForm that allows a librarian to add a new book to the library
class AddBookForm(FlaskForm):
    numberOfAuthors = IntegerField("Number of Authors:", validators=[DataRequired()])
    bookTitle = StringField("Book Title:", validators=[DataRequired(), Length(min=1, max=200)])
    genre = StringField("Genre:", validators=[DataRequired(), Length(min=1, max=40)])
    isbn13 = StringField("13 digit ISBN:", validators=[DataRequired(), Length(min=1, max=15)])
    yearPublished = DateField("Year of Publication:", format="%Y-%m-%d", validators=[DataRequired()])
    blurb = TextAreaField("Book Blurb:", validators=[DataRequired(), Length(min=1, max=2000)])
    minYearGroup = RadioField("Minimum Year Group Allowed:", choices=[("7", "Year 7"), ("8", "Year 8"), ("9", "Year 9"), ("10", "Year 10"), ("11", "Year 11"), ("12", "Year 12"), ("13", "Year 13"), ("0", "Staff")])
    accessionNumber = StringField("Accession Number:", validators=[DataRequired(), Length(min=1, max=10)])
    coverImageLink = StringField("Cover Image URL:", validators=[DataRequired()])
    numberOfCopies = IntegerField("Number of Copies:", validators=[DataRequired()])
    addBook = SubmitField("Add Book")   

# Defines a FlaskForm class called ReportForm that allows a librarian to select whether they would like to view an existing report or would like to create a new report
class ReportForm(FlaskForm):
    newReportChoice = SelectField("Select a New Report", choices=[("topreadersgenretime", "Top X Readers in Y Genre in Z Time Period"), ("overdue", "Overdue Report"), ("topreadersyeargroup", "Top X Readers in Y Year Group"), ("None", "None")], validators=[Optional()])
    oldReportChoice = SelectField("Select an existing report:", choices=[], validators=[Optional(), Length(min=1, max=150)])
    select = SubmitField("Select Report")

# Defines a FlaskForm class called TopReadersGenreTimeForm that allows a librarian to create this type of report by entering in their desired parameters
class TopReadersGenreTimeForm(FlaskForm):
    number = IntegerField("Number of Readers:", validators=[DataRequired()])
    genre = StringField("Genre:", validators=[DataRequired()])
    startDate = DateField("Start Date:", validators=[DataRequired()])
    endDate = DateField("End Date:", validators=[DataRequired()])
    enter = SubmitField("Enter Information")

# Defines a FlaskForm class called TopReadersYearGroupForm that allows a librarian to create this type of report by entering in their desired parameters    
class TopReadersYearGroupForm(FlaskForm):
    number = IntegerField("Number of Readers:", validators=[DataRequired()])
    yearGroup = SelectField("Year Group:", choices=[("7", "2nd Form"), ("8", "3rd Form"), ("9", "Lower 4th"), ("10", "Upper 4th"), ("11", "5th Form"), ("12", "Lower 6th"), ("13", "Upper 6th"), ("0", "Staff"), ("1", "Librarian")])
    startDate = DateField("Start Date:", validators=[DataRequired()])
    endDate = DateField("End Date:", validators=[DataRequired()])
    enter = SubmitField("Enter Information")

# Defines a FlaskForm class called OverdueReportForm that allows a librarian to choose how many days overdue loans they would like to select to create overdue notices for
class OverdueReportForm(FlaskForm):
    days = IntegerField("Select Reports that are X days overdue:", validators=[DataRequired()])
    enter = SubmitField("Enter Information")

# Defines a FlaskForm class called UpdateDetailsForm that allows a librarian to optionally change a certain account information for a reader
class UpdateDetailsForm(FlaskForm):
    readerFirstName = StringField("First Name:", validators=[Optional(), Length(min=1, max=15)])
    readerLastName = StringField("Last Name:", validators=[Optional(), Length(min=1, max=15)])
    readerUsername = StringField("Enter a Username:", validators=[Optional(), Length(min=1, max=15)])
    readerSchoolEmailAddress = StringField("School Email Address:", validators=[Optional(), Length(min=1, max=25), userManagement.schoolEmailValidator])
    readerPersonalEmailAddress = StringField("Personal Email Address:", validators=[Optional(), Length(min=1, max=25), userManagement.personalEmailValidator])
    readerYearGroup = SelectField("Year Group:", choices=[("7", "2nd Form"), ("8", "3rd Form"), ("9", "Lower 4th"), ("10", "Upper 4th"), ("11", "5th Form"), ("12", "Lower 6th"), ("13", "Upper 6th"), ("0", "Staff"), ("1", "Librarian")], validators=[Optional()])
    readerHouseroom = SelectField("Houseroom:", choices=[('Le1a', 'Le1a'), ('Le1b', 'Le1b'), ('Le2', 'Le2'), ('Le3', 'Le3'), ('Le4', 'Le4'), ('Le5', 'Le5'), ('Le6', 'Le6'), ('Le7', 'Le7'),  ('Wa1a', 'Wa1a'), ('Wa1b', 'Wa1b'), ('Wa2', 'Wa2'), ('Wa3', 'Wa3'), ('Wa4', 'Wa4'), ('Wa5', 'Wa5'), ('Wa6', 'Wa6'), ('Wa7', 'Wa7'),  ('Ca1a', 'Ca1a'), ('Ca1b', 'Ca1b'), ('Ca2', 'Ca2'), ('Ca3', 'Ca3'), ('Ca4', 'Ca4'), ('Ca5', 'Ca5'), ('Ca6', 'Ca6'), ('Ca7', 'Ca7'),  ('Ch1a', 'Ch1a'), ('Ch1b', 'Ch1b'), ('Ch2', 'Ch2'), ('Ch3', 'Ch3'), ('Ch4', 'Ch4'), ('Ch5', 'Ch5'), ('Ch6', 'Ch6'), ('Ch7', 'Ch7'),  ('Ma1a', 'Ma1a'), ('Ma1b', 'Ma1b'), ('Ma2', 'Ma2'), ('Ma3', 'Ma3'), ('Ma4', 'Ma4'), ('Ma5', 'Ma5'), ('Ma6', 'Ma6'), ('Ma7', 'Ma7'),  ('Wi1a', 'Wi1a'), ('Wi1b', 'Wi1b'), ('Wi2', 'Wi2'), ('Wi3', 'Wi3'), ('Wi4', 'Wi4'), ('Wi5', 'Wi5'), ('Wi6', 'Wi6'), ('Wi7', 'Wi7')], validators=[Optional()])
    update = SubmitField("Update")

# The Flask before_request decorator will run the view function before_request before each request
@app.before_request
# The before_request() view function checks if the request endpoint is 'logout' and if so it clears all the variables stored in the session when the user logs in
def before_request():
    if request.endpoint in ['logout']:
        session.pop('user_type', None)
        session.pop('username', None)
        session.pop('logged_in', None)
        session.pop('readerID', None)

# The Flask context_processor will add variables to the context of all the templartes in the app, so they are not limited to the scope of one route
@app.context_processor
# The view function injectGlobalVariables returns a dictionary of two global variables - loggedIn a boolean value signfiying whether a reader is logged into the system and numNotifications which signifies the number of unread notifications for that reader
def injectGlobalVariables():
    loggedIn = session.get('logged_in', False)
    # Checks if the readerID is in the session and if it is retrieves the number of notifications for that reader
    if 'readerID' in session:
        readerID = session['readerID']
        notifications, _ = notificationManager.getNotificationsForReader(readerID)
        numNotifications = len(notifications)
    # Otherwise sets number of notifications to 0
    else:
        numNotifications = 0 
    
    return dict(loggedIn=loggedIn, numNotifications=numNotifications)

# Decorator and view function to render a welcompage.html template when a GET request is made to the "/" URL
@app.route("/")
def welcome():
    return render_template("welcomepage.html")

# Login decorator and view function to handle both GET and POST requests
@app.route("/login", methods=["GET", "POST"])
def login():
    # Initialise an instance of LoginForm
    loginForm = LoginForm()
    
    # Check the number of login attempts stored in session - if 3 ateempts and still not logged in redirect user to the enterEmail route to change their password
    loginAttempts = session.get('login_attempts', 0)
    if loginAttempts >= 2:
        session.pop('login_attempts', None)
        return redirect(url_for('enterEmail'))
    
    # If loginForm is submitted and validated
    if loginForm.validate_on_submit():
        # Clear the session of any remaining session variables if previous user didn't logout
        session.pop('user_type', None)
        session.pop('username', None)
        session.pop('logged_in', None)
        session.pop('readerID', None)
        # Retrieve entered username, password and admin code if there is one
        username = loginForm.enteredUsername.data
        password = loginForm.enteredPassword.data
        # Set the readerID by retrieveing associated readerID for input username
        readerID = reader.setAndGetReaderID(username)
        session['readerID'] = readerID
        # If admin code not provided set it to None
        if loginForm.enteredAdminCode.data == "":
            adminCode = None
            # Try to log in the reader, if successful set session variables and redirect user to the home page route
            if reader.loginReader(password, adminCode) == 1:
                session['user_type'] = "reader"
                session['username'] = username
                session['logged_in'] = True
                session.pop('login_attempts', None)
                notificationManager.notifyLoanToReturn(readerID)
                notificationManager.overdueLoan(readerID)
                return redirect(url_for('home'))
            # If unsuccessful log in, increment login attempts by 1 and render the login page route again
            else:
                session['login_attempts'] = loginAttempts + 1
                return render_template("loginpage.html", loginForm=loginForm)
        else:
            # If admin code provided set admin code to input data
            adminCode = loginForm.enteredAdminCode.data
            # Try to log in the reader, if successful set session variables and redirect user to the home page route
            if reader.loginReader(password, adminCode) == 1:
                session['user_type'] = "librarian"
                session["username"] = username
                session['logged_in'] = True
                session.pop('login_attempts', None)
                notificationManager.overdueLoan(readerID)
                notificationManager.notifyLoanToReturn(readerID)
                return redirect(url_for('home'))
            # If unsuccessful log in, increment login attempts by 1 and render the login page route again
            else:
                session['login_attempts'] = loginAttempts + 1
                return render_template("loginpage.html", loginForm=loginForm)
            
    # Render the loginpage.html template and pass loginForm as template variable
    return render_template("loginpage.html", loginForm=loginForm)

# Register decorator and view function to handle both GET and POST requests
@app.route("/register", methods=["GET", "POST"])
def register():
    # Intialise an instance of RegistrationForm
    registerForm = RegistrationForm()
    firstName=""
    if registerForm.validate_on_submit():
        # If reader's input password data does not match their input confirm password data, flash a message on the screen and redirect to the register page again
        if registerForm.readerPassword.data != registerForm.confirmPassword.data:
            flash("Passwords must match.")
            return redirect(url_for('register'))
        else:
        # Retrieve the reader's input data to the form
            firstName = registerForm.readerFirstName.data
            lastName = registerForm.readerLastName.data
            username = registerForm.readerUsername.data
            password = registerForm.readerPassword.data
            schoolEmailAddress = registerForm.readerSchoolEmailAddress.data
            personalEmailAddress = registerForm.readerPersonalEmailAddress.data
            dateOfBirth = registerForm.readerDateOfBirth.data
            yearGroup = registerForm.readerYearGroup.data
            houseroom = registerForm.readerHouseroom.data
            # If no admin code provided set it to None
            if registerForm.readerAdminCode.data == "":
                adminCode = None
                # Attempt to register new account for reader 
                reader.registerNewReader(firstName, lastName, username, password, schoolEmailAddress, personalEmailAddress, dateOfBirth, yearGroup, houseroom, adminCode)
                # Redirect to success route and display a message for successful login
                return redirect(url_for('success', firstname=firstName))
            else:
            # Retrieve the input admin code by the reader
                adminCode = registerForm.readerAdminCode.data
                # Attempt to register new account for reader as a librarian
                if reader.registerNewReader(firstName, lastName, username, password, schoolEmailAddress, personalEmailAddress, dateOfBirth, yearGroup, houseroom, adminCode) == 0:
                    # If incorrect admin code display message and redirect to the register route again
                    flash("Unauthorised admin code - register again.")
                    return redirect(url_for('register'))
                else:
                    # Redirect to success route and display a message for successful login
                    return redirect(url_for('success', firstname=firstName))
    # Render the registerpage.html template and pass registerForm as a template variable
    return render_template("registerpage.html", registerForm=registerForm)

# Decorator and view function to render a success.html template on GET request
@app.route("/success/<firstname>")
def success(firstname):
    return render_template("success.html", firstname=firstname)

# Home decorator and view function to handle GET requests
@app.route("/home")
def home():
    # If username is in session, set session variables
    if 'username' in session:
        username = session['username']
        userType = session['user_type']
        # Call the getLeaderboard method to pass leaderboard as variable to template
        leaderboard = reader.getLeaderboard()
        # Get current month for leaderboard
        today = date.today()
        currentMonth = today.strftime("%B")
        # Render the homepage.html template and pass in username, userType, leaderboard and currentMonth as template variables
        return render_template("homepage.html", username=username, userType=userType, leaderboard=leaderboard, currentMonth=currentMonth)
    else:
    # If username not in session display message and redirect user to login route
        flash("To access the home page you must login first.")
        return redirect(url_for('login'))

# Browsebooks decorator and view function to handle GET and POST requests
@app.route("/browsebooks", methods=["GET", "POST"])
def browsebooks():
    # Initialise an instance of SearchForm
    searchForm = SearchForm()
    # Initially set searchResults to empty string
    searchResults = ""
    # Retrieve new books that were added to library database in last year
    today = date.today()
    yearago = today - datetime.timedelta(days=365)
    newBooks = book.getNewBooks(yearago.strftime("%Y-%m-%d"))
    # Retrieve personalised recommendations for reader
    readerID = session['readerID']
    recommendedBooks = book.getRecommendedBooks(readerID) 
    print(recommendedBooks)  
    # Retrieve popular books 
    popularBooks = book.getPopularBooks()
    # Retrieve books for each of the genres
    genres = ["classic", "fiction", "dystopian"]
    # Create a list of tuples, where first value of each tuple is title of bookshelf and second value is list of books in that shelf
    bookshelves = [('Popular', popularBooks)]
    for genre in genres: 
        bookshelves.append((genre.capitalize(), book.getBookInGenre(genre)))
    
    if searchForm.validate_on_submit():
        orderbyfield = searchForm.orderByField.data
        orderbydirection = searchForm.orderByDirection.data
        # If the reader has searched by searchString retrieve the input string
        if searchForm.searchString.data:
            searchString = searchForm.searchString.data
            # Search for matching books and store in searchResults
            searchResults = book.searchBook(orderbyfield, orderbydirection, searchString)
            # Render browsebooks.html template and pass as template variables searchForm, searchResults, newBooks and bookshelves
            return render_template("browsebooks.html", searchForm=searchForm, searchResults=searchResults, newBooks=newBooks, bookshelves=bookshelves)
        else:
            # If reader has chosen to search by advanced search, retrieve data from form fields
            authorfirstname = searchForm.authorFirstName.data
            authorlastname = searchForm.authorLastName.data
            booktitle = searchForm.bookTitle.data
            bookisbn = searchForm.bookISBN.data
            bookgenre = searchForm.bookGenre.data
            # Search for matching books and store in searchResults
            searchResults = book.searchBook(orderbyfield, orderbydirection, authorfirstname, authorlastname, booktitle, bookisbn, bookgenre)
            # Render browsebooks.html template and pass as template variables searchForm, searchResults, newBooks and bookshelves
            return render_template("browsebooks.html", searchForm=searchForm, searchResults=searchResults, newBooks=newBooks, bookshelves=bookshelves)
    
    return render_template("browsebooks.html", searchForm=searchForm, searchResults=searchResults, newBooks=newBooks, recommendedBooks=recommendedBooks, bookshelves=bookshelves)

# Bookinfo decorator and view function to handle both GET and POST Requests
# Takes route parameters of bookID
@app.route("/bookInfo/<int:bookID>", methods=["GET", "POST"])
def bookInfo(bookID):
    # Get book information for book with bookID
    bookinfo = book.getBookInfo(bookID)
    # Get reviews and rating distribution for book
    bookReviews, ratingPercentage = review.getBookReviews(bookID)
    # Initialise an instance of ReadingListForm
    readingListForm = ReadingListForm()
    readerID = session['readerID']
    # Populate choices attribute of readingList field of form with readerID existing reading list titles
    readingListForm.readingList.choices = readingList.getReadingListChoices(readerID)
    # Retrieve titles of all reading lists that feature this book
    tags = readingList.getReadingListsForBook(bookID)
    # If submitted and validates POST request
    if readingListForm.validate_on_submit():
        # Retrieve form field data
        read = readingListForm.readOrNot.data
        # If reader adding book to new reading list
        if readingListForm.newList.data:
            newList = readingListForm.newList.data
            readingList.addToNewReadingList(readerID, newList, bookID, read)
            # Display success message and redirect to bookInfo route
            flash(f"You have successfully added {bookinfo[0][2]} to {newList}")
            return redirect(url_for("bookInfo", bookID=bookID))
        else:
        # If reader adding book to existing reading list
            readingListChoice = readingListForm.readingList.data
            readerID = session['readerID']
            readingList.addToExistingReadingList(readerID, readingListChoice, bookID, read)
            # Display success message and redirect to bookInfo route
            flash(f"You have successfully added {bookinfo[0][2]} to {readingListChoice}")
            return redirect(url_for("bookInfo", bookID=bookID))
        
    # Render template for bookinfo.html and pass the template variables bookinfo, bookReviews, ratingPercentage, readingListForm and tags
    return render_template("bookInfo.html", bookinfo=bookinfo, bookReviews=bookReviews, ratingPercentage=ratingPercentage, readingListForm=readingListForm, tags=tags)

# Loanbook decorator and view function to handle GET Requests
# Takes route parameters of bookID and bookTitle
@app.route("/loanbook/<int:bookID>/<string:bookTitle>")
def loanbook(bookID, bookTitle):
    # Call loan book function to loan book with bookID
    readerID = session['readerID']
    loan.loanBook(readerID, bookID, bookTitle)
    # Redirect user to browsebooks route
    return redirect(url_for("browsebooks"))

# Reservebook decorator and view function to handle GET Requests
# Takes route parameters of bookID and bookTitle
@app.route("/reservebook/<int:bookID>/<string:bookTitle>")
def reservebook(bookID, bookTitle):
    # Call reserve book function to reserve book with bookID
    readerID = session['readerID']
    reservation.reserveBook(readerID, bookID)
    # Redirect user to browsebooks route
    flash(f"You have successfully reserved {bookTitle}")
    return redirect(url_for("browsebooks"))

# Readinglists decorator and view function to handle GET requests
@app.route("/readinglists")
def readinglists():
    # Retrieve all created reading lists for user with readerID
    readerID = session['readerID']
    readingLists = readingList.getReadingLists(readerID)
    # Render readinglists.html template and pass template variable of readingLists
    return render_template("readinglists.html", readingLists=readingLists)

# Viewloans decorator and view function to handle GET requests
@app.route("/viewloans")
def viewloans():
    # Retrieve all active loans for reader
    readerLoans = loan.getLoans()
    # Render viewloans.html template and pass template variable of readerLoans
    return render_template("viewloans.html", readerLoans=readerLoans)

# Viewreservations decorator and view function to handle GET requests
@app.route("/viewreservations")
def viewreservations():
    # Retrieve all pending reservations for reader
    reservations = reservation.getReservations()
    # Render viewreservations.html template and pass reservations template variable
    return render_template("viewreservations.html", reservations=reservations)

# Cancelreservation decorator and view function to handle GET requests
# Takes route parameters of bookID and reservationID
@app.route("/cancelreservation/<int:bookID>/<int:reservationID>")
def cancelreservation(bookID, reservationID):
    # Cancels reader's reservation for bookID
    title = reservation.cancelReservation(bookID, reservationID)
    # Display cancellation message and redirect user to viewreservations route
    flash(f"You have cancelled your reservation for {title}")
    return redirect(url_for("viewreservations"))

# Returnloan decorator and view function to handle GET requests
# Takes route parameters of loanID and copyID and bookID
@app.route("/returnloan/<int:loanID>/<int:copyID>/<int:bookID>")
def returnloan(loanID, copyID, bookID):
    # Return reader's loan for bookID
    title = loan.returnLoan(loanID, copyID, bookID)
    # Display success message and redirect user to viewloans route
    flash(f"You have successfully returned {title}.")
    return redirect(url_for("viewloans"))

# Viewnotifications decorator and view function to handle GET requests
@app.route("/viewnotifications")
def viewnotifications():
    readerID = session['readerID']
    # Retrieves all unread notifications for a reader
    notifications, notificationIDs = notificationManager.getNotificationsForReader(readerID)
    # Once unread notifications stored in notifications variable, all unread notifications for that reader are marked as Read
    notificationManager.markNotificationsAsViewed(notificationIDs)
    # Render viewnotifications.html template and pass notifications as a template variable
    return render_template("viewnotifications.html", notifications=notifications)
 
# Viewbooks decorator and view function to handle GET and POST requests 
@app.route("/viewbooks", methods=["GET", "POST"])
def viewbooks():
    # Initialise an instance of searchForm
    searchForm = SearchForm()
    searchResults = ""
    if searchForm.validate_on_submit():
        # Retrieve all form field data
        orderbyfield = searchForm.orderByField.data
        orderbydirection = searchForm.orderByDirection.data
        if searchForm.searchString.data:
            # Librarian can search for book by string
            searchString = searchForm.searchString.data
            searchResults = book.searchBook(orderbyfield, orderbydirection, searchString)
            return render_template("viewbooks.html", searchForm=searchForm, searchResults=searchResults)
        else:
            # Librarian can search for book by specific fields
            authorfirstname = searchForm.authorFirstName.data
            authorlastname = searchForm.authorLastName.data
            booktitle = searchForm.bookTitle.data
            bookisbn = searchForm.bookISBN.data
            bookgenre = searchForm.bookGenre.data
            searchResults = book.searchBook(orderbyfield, orderbydirection, authorfirstname, authorlastname, booktitle, bookisbn, bookgenre)
            return render_template("viewbooks.html", searchForm=searchForm, searchResults=searchResults)
        
    # Return render template viewbooks.html and pass as template variables searchForm and searchResults
    return render_template("viewbooks.html", searchForm=searchForm, searchResults=searchResults)

# Deletebook decorator and view function to handle GET requests
# Takes route parameters of bookID and bookTitle
@app.route("/deletebook/<int:bookID>/<string:bookTitle>")
def deletebook(bookID, bookTitle):
    # 'Deletes' a book with bookID from the library
    book.deleteBook(bookID)
    # Display success message to the reader and redirect user to viewbooks route
    flash(f"You have successfully removed all copies of {bookTitle} from the library database")
    return redirect(url_for("viewbooks"))

# Returnloan decorator and view function to handle GET and POST requests
@app.route("/addbook", methods=["GET", "POST"])
def addbook():
    # Initialise an instance of AddBookForm
    addBookForm = AddBookForm()
    # Get all existing authors and publishers in database to populate HTML select fields in addbook.html template
    publisherOptions = book.getPublisherOptions()
    authorOptions = book.getAuthorOptions()
    if addBookForm.validate_on_submit():
        # Retrieve all form fields' data
        title = addBookForm.bookTitle.data
        genre = addBookForm.genre.data
        isbn13 = addBookForm.isbn13.data
        yearPublished = addBookForm.yearPublished.data
        blurb = addBookForm.blurb.data
        minYearGroup = addBookForm.minYearGroup.data
        coverImageLink = addBookForm.coverImageLink.data
        numberOfCopies = addBookForm.numberOfCopies.data
        accessionNumber = addBookForm.accessionNumber.data
        publisher = request.form["publisher"]
        numberOfAuthors = addBookForm.numberOfAuthors.data
        # Retrieve author data from request object for mulitple authors
        bookAuthors = []
        for i in range(numberOfAuthors):
            authorKey = 'author_' + str(i)
            bookAuthor = request.form[authorKey]
            bookAuthors.append(bookAuthor)
        # Call addBook method to add book to library and redirect librarian to home route
        book.addBook(title, genre, isbn13, yearPublished, publisher, bookAuthors, blurb, minYearGroup, coverImageLink, numberOfCopies, accessionNumber)
        return(redirect(url_for('home')))
    # Render template for addbook.html and pass template variables of addBookForm, publisherOptions and authorOptions
    return render_template("addbook.html", addBookForm=addBookForm, publisherOptions=publisherOptions, authorOptions=authorOptions)

# Leavereview decorator and view function to handle GET and POST requests
# Takes route parameters of bookID and bookTitle   
@app.route("/leavereview/<int:bookID>/<string:bookTitle>", methods=["GET", "POST"])
def leavereview(bookID, bookTitle):
    # Initialise an instance of ReviewForm
    reviewForm = ReviewForm()
    if reviewForm.validate_on_submit():
        # Retrive data from form fields and request object
        reviewtext = reviewForm.reviewText.data
        rating = request.form["rating"]
        username = session['username']
        readerID = session['readerID']
        if bookID is not None:
            # Leave a review for book and flash success message and redirect user to bookInfo route
            review.leaveReview(readerID, reviewtext, rating, bookID)
            flash(f"Hi {username}. You have successfully left a review for {bookTitle}!")
            return redirect(url_for("bookInfo", bookID=bookID))
        else:
            # Display unsuccessful message to reader and redirect to leavereview route again
            flash("Failed to leave a review. Please try again.")
            return redirect(url_for("leavereview.html", reviewForm=reviewForm, bookID=bookID, bookTitle=bookTitle))
    # Render template for leavereview.html and pass template variables of reviewForm, bookID and bookTitle  
    return render_template("leavereview.html", reviewForm=reviewForm, bookID=bookID, bookTitle=bookTitle)

# Accountdetails decorator and view function to handle GET requests
@app.route("/accountdetails")
def accountdetails():
    # Fetch current account details for reader
    accountDetails = reader.getCurrentAccountDetails()
    # Render template for acccountdetails.html and pass template variable of accountDetails
    return render_template("accountdetails.html", accountDetails=accountDetails)

# Manageaccounts decorator and view function to handle GET and POST requests
@app.route("/manageaccounts", methods=["GET", "POST"])
def manageaccounts():
    # Initialise an instance of ReaderSearchForm
    readerSearchForm = ReaderSearchForm()
    readerSearchResults = ""
    if readerSearchForm.validate_on_submit():
        # Search for reader according to input data and fetch results
        name = readerSearchForm.readerName.data
        readerSearchResults = reader.searchReader(name)
        return render_template("manageaccounts.html", readerSearchForm=readerSearchForm, readerSearchResults=readerSearchResults)
    # Render template for manageaccounts.html and pass readerSearchForm and readerSearchResults as variables
    return render_template("manageaccounts.html", readerSearchForm=readerSearchForm, readerSearchResults=readerSearchResults)

# Deletereader decorator and view function to handle GET requests
# Takes route parameter of readerID
@app.route("/deletereader/<int:readerID>")
def deletereader(readerID):
    # Delete a reader from database and display success message
    reader.deleteReader(readerID)
    flash("Reader successfully deleted from library database.")
    # Redirect user to manageaccounts route
    return redirect(url_for("manageaccounts"))

# Loansandreservations decorator and view function to handle GET requests
# Takes route parameter of readerID
@app.route("/loansandreservations/<int:readerID>")
def loansandreservations(readerID):
    # Retrieve all active loans and all pending reservations for readerID
    readerLoans = loan.getLoans(readerID)
    readerReservations = reservation.getReservations(readerID)
    # Render template for loansandreservations.html and pass readerLoans and readerReservations as template variables
    return render_template("loansandreservations.html", readerLoans=readerLoans, readerReservations=readerReservations)

# Updatereader decorator and view function to handle GET and POST requests
# Takes route parameter of readerID
@app.route("/updatereader/<int:readerID>", methods=["GET", "POST"])
def updatereader(readerID):
    # Initialise instance of UpdateDetailsForm
    updateDetailsForm = UpdateDetailsForm()
    # Fetch current account details for reader
    currentAccountDetails = reader.getCurrentAccountDetails(readerID)
    if updateDetailsForm.validate_on_submit():
        # For form fields, if data provided store data in variable otherwise set variable to None
        if updateDetailsForm.readerFirstName.data:
            firstname = updateDetailsForm.readerFirstName.data
        else:
            firstname = None
        if updateDetailsForm.readerLastName.data:
            lastname = updateDetailsForm.readerLastName.data
        else:
            lastname = None 
        if updateDetailsForm.readerUsername.data:
            username = updateDetailsForm.readerUsername.data
        else:
            username = None
        if updateDetailsForm.readerPersonalEmailAddress.data:
            personalemail = updateDetailsForm.readerPersonalEmailAddress.data
        else:
            personalemail = None
        if updateDetailsForm.readerSchoolEmailAddress.data:
            schoolemail = updateDetailsForm.readerSchoolEmailAddress.data
        else:
            schoolemail = None
        if updateDetailsForm.readerYearGroup.data:
            yeargroup = updateDetailsForm.readerYearGroup.data
        else:
            yeargroup = None
        if updateDetailsForm.readerHouseroom.data:
            houseroom = updateDetailsForm.readerHouseroom.data
        else:
            houseroom = None
        # Update reader's account details and display success message
        reader.updateAccountDetails(readerID, firstname, lastname, username, personalemail, schoolemail, yeargroup, houseroom)
        flash("Reader details updated successfully.")
        # Redirect librarian to manageaccounts route
        return redirect(url_for("manageaccounts"))
    # Render template for updatereader.html and pass currentAccountDetails updateDetailsForm and readerID as template variables
    return render_template("updatereader.html", currentAccountDetails=currentAccountDetails, updateDetailsForm=updateDetailsForm, readerID=readerID)

# Viewreviews decorator and view function to handle GET requests  
@app.route("/viewreviews")
def viewreviews():
    # Retrieve all reviews made by a reader
    readerID = session['readerID']
    readerReviews = review.getReaderReviews(readerID)
    # Render viewreviews.html tempalte and pass readerReviews as a template variable
    return render_template("viewreviews.html", readerReviews=readerReviews)

# Reports decorator and view function to handle GET and POST requests  
@app.route("/reports", methods=["GET", "POST"])
def reports():
    # Initialise an instance of ReportForm
    reportForm = ReportForm()
    # Populate the choices attribute of the oldReportChoice field with the titles of all past reports
    reportForm.oldReportChoice.choices = report.getAllPastReportTitles()
    if reportForm.validate_on_submit():
        # If librarian has chosen to create a new report
        if reportForm.newReportChoice.data != "None":
            choice = reportForm.newReportChoice.data
            # Redirect to route of report choice
            if choice == "topreadersgenretime":
                return redirect(url_for('topreadersgenretime'))
            elif choice == "topreadersyeargroup":
                return redirect(url_for('topreadersyeargroup'))
            elif choice == "overdue":
                return redirect(url_for("overduereports"))
        else:
        # If librarian has chosen existing report
            choice = reportForm.oldReportChoice.data
            # Retrieve reportID for past report with choice as title
            reportID = report.getExistingReportByTitle(choice)
            # Store reportID in session
            session['reportID'] = reportID
            # Redirect user to view report route
            return redirect(url_for('viewreport'))
    # Render template for reports.html and pass reportForm as template variable
    return render_template("reports.html", reportForm=reportForm)

# Overduereports decorator and view function to handle GET and POST requests  
@app.route("/overduereports", methods=["GET", "POST"])
def overduereports():
    # Initialise an instance of OverdueReportForm
    overdueReportForm = OverdueReportForm()
    if overdueReportForm.validate_on_submit():
        # Retrieve form data
        days = overdueReportForm.days.data
        # Generate report and return its reportID
        reportID = report.getOverdueLoanReports(days)
        # Store reportID in session
        session['reportID'] = reportID
        # Redirect user to view report route
        return redirect(url_for('viewreport'))
    # Render template for overduereport.html and pass overdueReportForm as template variable
    return render_template("overduereport.html", overdueReportForm=overdueReportForm)

# Topreadersgenretime decorator and view function to handle GET and POST requests    
@app.route("/topreadersgenretime", methods=["GET", "POST"])
def topreadersgenretime():
    # Initialise an instance of TopReadersGenreTimeForm
    topReadersGenreTimeForm = TopReadersGenreTimeForm()
    if topReadersGenreTimeForm.validate_on_submit():
        # Retrieve submitted form data
        numberOfReaders = topReadersGenreTimeForm.number.data
        genre = topReadersGenreTimeForm.genre.data
        startDate = topReadersGenreTimeForm.startDate.data
        endDate = topReadersGenreTimeForm.endDate.data
        # Generate report and return its reportID 
        reportID = report.getTopReadersGenreTime(numberOfReaders, genre, startDate, endDate)
        # Store reportID in session
        session['reportID'] = reportID
        # Redirect user to view report route
        return redirect(url_for('viewreport'))
    # Render template for topreadersgenretime.html and pass topReadersGenreTimeForm as template variable      
    return render_template("topreadersgenretime.html", topReadersGenreTimeForm=topReadersGenreTimeForm)

# Topreadersgenretime decorator and view function to handle GET and POST requests   
@app.route("/topreadersyeargroup", methods=["GET", "POST"])
def topreadersyeargroup():
    # Initialise an instance of TopReadersYearGroupForm
    topReadersYearGroupForm = TopReadersYearGroupForm()
    if topReadersYearGroupForm.validate_on_submit():
        # Retrieve submitted form data
        numberOfReaders = topReadersYearGroupForm.number.data
        yearGroup = topReadersYearGroupForm.yearGroup.data
        startDate = topReadersYearGroupForm.startDate.data
        endDate = topReadersYearGroupForm.endDate.data
        # Generate report and return its reportID 
        reportID = report.getTopReadersYearGroup(numberOfReaders, yearGroup, startDate, endDate)
        # Store reportID in session
        session['reportID'] = reportID
        # Redirect user to view report route
        return redirect(url_for('viewreport'))
    # Render template for topreadersyeargroup.html and pass topReadersYearGroupForm as template variable          
    return render_template("topreadersyeargroup.html", topReadersYearGroupForm=topReadersYearGroupForm)

# Downloadreport decorator and view function to handle GET requests
@app.route("/downloadreport")
def downloadreport():
    # Get reportID from session
    reportID = session['reportID']
    # Clear session of reportID
    session.pop('reportID', None)
    # Retrieve PDF bytes content for report with reportID
    reportPDF = report.getExistingReport(reportID)
    if reportPDF:
        # If no report retrieved - display error message
        if len(reportPDF) == 0:
            return "Error: The report could not be generated."
        else:
            # Send a PDF file to user, convert bytes stream to PDF and insert as embed link in viewreport route
            return send_file(
                BytesIO(reportPDF),
                download_name='report.pdf',
                mimetype='application/pdf',
                as_attachment=False)
    else:
        abort(404)

# Viewreport decorator and view function to handle GET requests
@app.route("/viewreport")
def viewreport():
    # Renders viewreport.html template which will display the PDF file from download report
    return render_template("viewreport.html")

# EnterEmail decorator and view function to handle GET and POST requests
@app.route("/enterEmail", methods=["GET", "POST"])
def enterEmail():
    # Initialise an instance of EnterEmailForm
    enterEmailForm = EnterEmailForm()
    if enterEmailForm.validate_on_submit():
        # Retrieve form data for entered emails
        personalEmail = enterEmailForm.enteredPersonalEmail.data
        schoolEmail = enterEmailForm.enteredSchoolEmail.data
        # Check if emails exist under account in database and if so redirect reader to changePassword route
        if userManagement.checkEmail(personalEmail, schoolEmail):
            return redirect(url_for('changePassword'))
        else:
        # If entered email addressses don't exist display an error message and redirect user to enterEmail route again
            flash("Email addresses not found. Please try again.")
            return redirect(url_for('enterEmail'))
    # Render template for enterEmail.html and pass enterEmailForm as template variable
    return render_template("enterEmail.html", enterEmailForm=enterEmailForm)

# ChangePassword decorator and view function to handle GET and POST requests
@app.route("/changePassword", methods=["GET", "POST"])
def changePassword():
    # Initialise an instance of the ChangePasswordForm
    changePasswordForm = ChangePasswordForm()
    if changePasswordForm.validate_on_submit():
        # If new password entered by the reader and confirmed password don't match display message to reader and redirect to changePassword again
        if changePasswordForm.newPassword.data != changePasswordForm.confirmPassword.data:
            flash("Passwords must match.")
            return redirect(url_for('changePassword'))
        else:
            # Retrieve form data and change reader's password
            username = changePasswordForm.username.data
            password = changePasswordForm.newPassword.data
            userManagement.changePassword(password)
            # Reset number of login attempts to 0
            session['login_attempts'] = 0
            if 'logged_in' in session:
                # If they changed password after logging in redirect back to account details route
                return redirect(url_for("accountdetails"))
            else:
                # If they changed password when attempting to long redirect to login route
                return redirect(url_for('login'))
    # Render template for changePassword.html and pass changePasswordForm as template variable   
    return render_template("changePassword.html", changePasswordForm=changePasswordForm)

# ChangeEmail decorator and view function to handle GET and POST requests
@app.route("/changeEmail", methods=["GET", "POST"])
def changeEmail():
    # Initialise an instance of ChangeEmailForm
    changeEmailForm = ChangeEmailForm()
    if changeEmailForm.validate_on_submit():
        # Retrieve form data
        personalEmail = changeEmailForm.personalEmail.data
        schoolEmail = changeEmailForm.schoolEmail.data
        # Check is school email is valid and if so change personal email, display success message and redirect to accountdetails route
        if userManagement.checkSchoolEmail(personalEmail, schoolEmail):
            flash("Personal email address successfully changed!")
            return redirect(url_for('accountdetails'))
        else:
        # Else display error message and redirect to changeEmail route again
            flash("School email address not found. Please try again.")
            return redirect(url_for('changeEmail'))
    # Render template for changeemail.html and pass changeEmailForm as template variable
    return render_template("changeemail.html", changeEmailForm=changeEmailForm)

# Logout decorator and view function to handle GET requests
@app.route("/logout")
def logout():
    # Clear session to remove user data
    session['logged_in'] = False
    session.clear()
    # Render template for logout.html
    return render_template("logout.html")

# If current script being run open Flask development server and run app
if __name__ == '__main__':
    app.run()