import sqlite3

# The filepath to the database is passed to the sqlite3 database connection object. This will allow me to perform operations on this database file.
con = sqlite3.connect('library.db')
# The cursor object is initialised which will allow me to execute commands on the database,
cur = con.cursor()

# This query will be executed and will create the Publisher table in the 'library.db' database

cur.execute("""
CREATE TABLE IF NOT EXISTS Publisher (
    PublisherID INTEGER PRIMARY KEY AUTOINCREMENT,
    PublisherName VARCHAR(30) NOT NULL
)           
            """)


# This query will be executed and will create the Author table in the 'library.db' database

cur.execute("""
CREATE TABLE IF NOT EXISTS Author (
    AuthorID INTEGER PRIMARY KEY AUTOINCREMENT,
    AuthorFirstName VARCHAR(20) NOT NULL,
    AuthorLastName VARCHAR(20) NOT NULL
);           
            """)


# This query will be executed and will create the AuthorBook table in the 'library.db' database

cur.execute("""
CREATE TABLE IF NOT EXISTS AuthorBook (
    AuthorID INTEGER,
    BookID INTEGER,
    FOREIGN KEY (AuthorID) REFERENCES Author (AuthorID),
    FOREIGN KEY (BookID) REFERENCES Book (BookID),
    PRIMARY KEY (AuthorID, BookID)    
);            
            """)


# This query will be executed and will create the Book table in the 'library.db' database

cur.execute("""
CREATE TABLE IF NOT EXISTS Book (
    BookID INTEGER PRIMARY KEY AUTOINCREMENT,
    ISBN VARCHAR(13) NOT NULL,
    Title VARCHAR(200) NOT NULL,
    Genre VARCHAR(40) NOT NULL,
    YearPublished DATE NOT NULL,
    PublisherID INTEGER,
    DateAdded DATE,
    Blurb VARCHAR(2000) NOT NULL,
    MinYearGroup INTEGER NOT NULL,
    CoverImageURL TEXT,
    FOREIGN KEY (PublisherID) REFERENCES Publisher (PublisherID)
);            
            """)


# This query will be executed and will create the BookCopy table in the 'library.db' database

cur.execute("""
CREATE TABLE IF NOT EXISTS BookCopy (
    CopyID INTEGER NOT NULL,
    BookID INTEGER NOT NULL,
    AccessionNumber VARCHAR(10) NOT NULL,
    Status VARCHAR(15),
    PRIMARY KEY (CopyID, BookID),
    FOREIGN KEY (BookID) REFERENCES Book (BookID)
);            
            """)


# This query will be executed and will create the Reader table in the 'library.db' database

cur.execute("""
CREATE TABLE IF NOT EXISTS Reader (
    ReaderID INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName VARCHAR(15) NOT NULL,
    LastName VARCHAR(15) NOT NULL,
    ReaderUsername VARCHAR(15) NOT NULL,
    ReaderSalt VARCHAR(15) NOT NULL,
    ReaderHash VARCHAR(20),
    SchoolEmailAddress VARCHAR(25) NOT NULL,
    PersonalEmailAddress VARCHAR(25) NOT NULL,
    DateOfBirth DATE NOT NULL,
    YearGroup INTEGER NOT NULL,
    Houseroom VARCHAR (15) NOT NULL,
    AdminCode VARCHAR(5)  
);          
            """)


# This query will be executed and will create the Reservation table in the 'library.db' database

cur.execute("""
CREATE TABLE IF NOT EXISTS Reservation (
    ReservationID INTEGER PRIMARY KEY AUTOINCREMENT,
    CopyID INTEGER NOT NULL,
    BookID INTEGER NOT NULL,
    ReaderID INTEGER NOT NULL,
    ReservationStatus VARCHAR(10) NOT NULL,
    ReservationTimestamp DATE DEFAULT CURRENT_TIMESTAMP,
    QueuePosition INTEGER,
    Priority INTEGER,
    FOREIGN KEY (CopyID) REFERENCES BookCopy (CopyID),
    FOREIGN KEY (BookID) REFERENCES Book (BookID),
    FOREIGN KEY (ReaderID) REFERENCES Reader (ReaderID)
);            
            """)


# This query will be executed and will create the Loan table in the 'library.db' database

cur.execute("""
CREATE TABLE IF NOT EXISTS Loan (
    LoanID INTEGER PRIMARY KEY AUTOINCREMENT,
    CopyID INTEGER NOT NULL,
    BookID INTEGER NOT NULL,
    ReaderID INTEGER NOT NULL,
    LoanStartDate DATE NOT NULL,
    LoanEndDate DATE NOT NULL,
    LoanStatus VARCHAR(15) NOT NULL,
    FOREIGN KEY (CopyID) REFERENCES BookCopy (CopyID),
    FOREIGN KEY (BookID) REFERENCES Book (BookID),
    FOREIGN KEY (ReaderID) REFERENCES Reader (ReaderID)
);            
            """)

# This query will be executed and will create the Review table in the 'library.db' database

cur.execute("""
CREATE TABLE IF NOT EXISTS Review (
    ReviewID INTEGER PRIMARY KEY AUTOINCREMENT,
    BookID INTEGER NOT NULL,
    ReaderID INTEGER NOT NULL,
    ReviewText VACRHAR(1000) NOT NULL,
    Rating INTEGER NOT NULL,
    DateReviewed DATE NOT NULL,
    FOREIGN KEY (BookID) REFERENCES Book (BookID),
    FOREIGN KEY (ReaderID) REFERENCES Reader (ReaderID)
);            
            """)

# This query will be executed and will create the ReadingList table in the 'library.db' database

cur.execute("""
CREATE TABLE IF NOT EXISTS ReadingList (
    ReadingListID INTEGER PRIMARY KEY AUTOINCREMENT,
    ReaderID INTEGER NOT NULL,
    ReadingListTitle VARCHAR(30) NOT NULL,
    FOREIGN KEY (ReaderID) REFERENCES Reader (ReaderID)
);            
            """)

# This query will be executed and will create the ReadingListBook table in the 'library.db' database

cur.execute("""
CREATE TABLE IF NOT EXISTS ReadingListBook (
    ReadingListID INTEGER NOT NULL,
    BookID INTEGER NOT NULL,
    Read BOOLEAN,
    PRIMARY KEY (ReadingListID, BookID),
    FOREIGN KEY (ReadingListID) REFERENCES ReadingList (ReadingListID),
    FOREIGN KEY (BookID) REFERENCES Book (BookID)
);           
            """)

# This query will be executed and will create the Notification table in the 'library.db' database

cur.execute(""" 
CREATE TABLE IF NOT EXISTS Notification (
    NotificationID INTEGER PRIMARY KEY AUTOINCREMENT,
    NotificationType VARCHAR(25) NOT NULL,
    Viewed BOOLEAN NOT NULL DEFAULT FALSE,
    ReaderID INTEGER NOT NULL,
    BookID INTEGER,
    ReservationID INTEGER,
    LoanID INTEGER,
    FOREIGN KEY (ReaderID) REFERENCES Reader (ReaderID),
    FOREIGN KEY (BookID) REFERENCES Book (BookID),
    FOREIGN KEY (ReservationID) REFERENCES Reservation (ReservationID),
    FOREIGN KEY (LoanID) REFERENCES Loan (LoanID)
);
""")


# This query will be executed and will create the Report table in the 'library.db' database

cur.execute("""
CREATE TABLE IF NOT EXISTS Report (
    ReportID INTEGER PRIMARY KEY AUTOINCREMENT,
    ReportTitle VARCHAR(150) NOT NULL,
    DateCreated DATE DEFAULT CURRENT_TIMESTAMP,
    PDFContent BLOB
);     
            """)


# This query will be executed and will populate the Publisher table with information about several Publishers. The PublisherIDs will be automatically addded when the query runs as the PublisherID field has an AUTOINCREMENT attribute.

cur.execute("""
INSERT INTO Publisher (PublisherName) VALUES 
('Penguin Classics'),
('J.B. Lippincott & Co.'),
('Alfred A. Knopf'),
('Delacorte Press'),
('Bloomsbury Publishing'),
('Little, Brown and Company'),
('Smith, Elder & Co.'),
('Secker & Warburg'),
('Chatto & Windus'),
('Faber and Faber'), 
('Charles Scribner''s Sons'),
('Simon & Schuster'),
('Penguin Books'),
('Harper Collins');            
            """)

# This query will be executed and will populate the Author table with information about several authors. The AuthorIDs will be automatically addded when the query runs as the AuthorID field has an AUTOINCREMENT attribute.

cur.execute("""
INSERT INTO Author (AuthorFirstName, AuthorLastName) VALUES 
('Jane', 'Austen'),
('Harper', 'Lee'),
('Markus', 'Zusak'),
('Karen', 'McManus'),
('Sarah J.', 'Maas'),
('J.D.', 'Salinger'),
('Charlotte', 'Brontë'),
('George', 'Orwell'),
('Aldous', 'Huxley'),
('William', 'Golding'),
('F.Scott', 'Fitzgerald'),
('Ray', 'Bradbury'),
('John', 'Steinbeck'),
('Veronica', 'Roth'),
('J.K.', 'Rowling');            
            """)

# This query will be executed and will populate the Book table with information about several books. The BookIDs are not provided as they will be automatically addded when the query runs as the BookID field has an AUTOINCREMENT attribute.

cur.execute("""
INSERT INTO Book (ISBN, Title, Genre, YearPublished, PublisherID, DateAdded, Blurb, MinYearGroup, CoverImageURL) VALUES 
('9780141439518', 'Pride and Prejudice', 'Classic Literature/Romance', '1813-01-28', 1, '2014-05-12', 'Pride and Prejudice is a romantic novel of manners written by Jane Austen in 1813. The novel follows the character development of Elizabeth Bennet, the dynamic protagonist of the book who learns about the repercussions of hasty judgments and eventually comes to appreciate the difference between superficial goodness and actual goodness. Set in early 19th-century England, the story offers poignant commentary on societal expectations, gender roles, and the institution of marriage.', 7, "https://m.media-amazon.com/images/I/81NLDvyAHrL._SY522_.jpg"),
('9780061120084', 'To Kill a Mockingbird', 'Fiction/Southern Gothic', '1960-07-11', 2, '2012-07-19', 'To Kill a Mockingbird, written by Harper Lee, is a classic novel that explores themes of racial injustice and moral growth. Set in the 1930s in the fictional town of Maycomb, Alabama, the story is narrated by Scout Finch, a young girl who learns about empathy, tolerance, and the complexities of human nature through her father''s defense of a black man falsely accused of rape.', 9, "https://m.media-amazon.com/images/I/51tDHl8Z7cL._AC_UF894,1000_QL80_.jpg"),
('9780375842207', 'The Book Thief', 'Historical Fiction', '2005-03-14', 3, '2018-02-14', 'The Book Thief, written by Markus Zusak, is a poignant story set in Nazi Germany during World War II. It follows the life of Liesel Meminger, a young girl who finds solace in stealing books and sharing them with others, including the Jewish man hiding in her basement. Narrated by Death, the novel explores themes of love, loss, and the power of words in the face of adversity.', 8, "https://m.media-amazon.com/images/I/71H2SJik5AL._AC_UF894,1000_QL80_.jpg"),
('9781524714680', 'One of Us Is Lying', 'Young Adult/Mystery', '2017-05-30', 4, '2017-06-27', 'One of Us Is Lying, written by Karen M. McManus, is a gripping young adult mystery novel that follows the aftermath of the sudden death of Simon, the creator of a notorious gossip app. As four classmates—each with their own secrets—become suspects, they must work together to uncover the truth behind Simon''s death before they are implicated in his murder.', 7, "https://m.media-amazon.com/images/I/81Moou8B7RL._AC_UF894,1000_QL80_.jpg"),
('9781619635180', 'A Court of Thorns and Roses', 'Fantasy/Romance', '2015-05-05', 5, '2016-08-09', 'A Court of Thorns and Roses, written by Sarah J. Maas, is a captivating fantasy novel that follows the journey of Feyre Archeron, a young huntress who is dragged into the perilous world of the faeries after killing a wolf in the woods. As Feyre navigates the dangerous politics of the faerie realm and uncovers dark secrets, she discovers the true extent of her own power and her capacity for love and sacrifice.', 10, "https://m.media-amazon.com/images/I/51dw+3CdtBL.jpg"),
('9780316769488', 'The Catcher in the Rye', 'Fiction/Literary Fiction', '1951-07-16', 6, '2020-01-05', 'The Catcher in the Rye, written by J.D. Salinger, is a controversial coming-of-age novel that follows the disillusioned teenager Holden Caulfield as he navigates the streets of New York City after being expelled from his prep school. Through Holden''s cynical and introspective narration, the novel explores themes of alienation, identity, and the loss of innocence in a post-war society.', 9, "https://m.media-amazon.com/images/I/91HPG31dTwL._AC_UF894,1000_QL80_.jpg"),
('9780141441146', 'Jane Eyre', 'Classic Literature/Gothic Fiction', '1847-10-16', 7, '2023-04-12', 'Jane Eyre, written by Charlotte Brontë, is a classic novel that follows the life of its eponymous heroine, Jane Eyre, from her tumultuous childhood to her eventual independence and self-discovery. Set in Victorian England, the novel explores themes of love, morality, and the search for belonging as Jane encounters challenges and confronts societal expectations in her quest for autonomy and fulfillment.', 7, "https://m.media-amazon.com/images/I/61RmfGsyCrL._AC_UF894,1000_QL80_.jpg"),
('9780451524935', '1984', 'Dystopian/Political fiction', '1949-06-08', 8, '2020-05-11','"1984" is a dystopian novel set in a totalitarian society where the government, led by the enigmatic figure Big Brother, exerts total control over every aspect of citizens'' lives. Winston Smith, a low-ranking member of the ruling Party, begins to question the oppressive regime and seeks to rebel against its pervasive surveillance and manipulation. Orwell''s chilling portrayal of a world stripped of individuality and freedom remains a haunting warning about the dangers of unchecked authoritarianism.' , 7, 'https://m.media-amazon.com/images/I/41B-RzZYAFL._SY445_SX342_.jpg'),
('9780060850524', 'Brave New World', 'Dystopian/Social science fiction', '1932-01-01', 9, '2022-07-09', '"Brave New World" presents a futuristic society where citizens are genetically engineered and conditioned to passively accept their roles, but one man challenges this conformity with disastrous consequences.', 10, 'https://encrypted-tbn0.gstatic.com/shopping?q=tbn:ANd9GcTOWv9GpMEJbadzFJ6jpvi56T1PYv1J00Hi74qKsVC5WeqtH0P27YqKyPFrpQSmX3n9ZgsUEsYvXmtfh6FDkHwnC-i0yI5cwhlaWmC3vSSR&usqp=CAc'),
('9780140283334', 'Lord of the Flies', 'Dystopian/Social Science/Allegorical', '1954-09-17', 10, '2021-10-18', '"Lord of the Flies" explores the dark side of human nature as a group of boys stranded on a deserted island descend into savagery and violence, revealing the fragility of civilization.', 9, 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1327869409i/7624.jpg'),
('9780141182636', 'The Great Gatsby', 'Tragedy/Social Commentary', '1992-05-05', 11, '2018-07-16', '"The Great Gatsby" follows the enigmatic millionaire Jay Gatsby as he pursues his lost love, Daisy Buchanan, in the opulent world of 1920s Long Island, exploring themes of love, wealth, and the American Dream.', 10, 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1490528560i/4671.jpg'),
('9781451673319', 'Fahrenheit 451', 'Dystopian/Science Fiction', '1953-10-19', 12, '2024-01-08', '"Fahrenheit 451" depicts a future society where books are banned, and "firemen" burn any that are found. Guy Montag, a fireman, begins to question his role and seeks to preserve knowledge and freedom.', 8, 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1383718290i/13079982.jpg'),
('9780141023571', 'Of Mice and Men', 'Tragedy/Classics/Historical Fiction', '1937-02-25', 13, '2024-01-09', '"Of Mice and Men" is a poignant tale of friendship and hardship during the Great Depression. George Milton and Lennie Small, two displaced ranch workers, dream of a better life, but tragic circumstances threaten their hopes.', 8, 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1511302904i/890.jpg'),
('9780062387244', 'Divergent', 'Dystopian/Young Adult', '2011-04-25', 14, '2024-03-11', 'In Beatrice Prior''s dystopian Chicago world, society is divided into five factions, each dedicated to the cultivation of a particular virtue—Candor (the honest), Abnegation (the selfless), Dauntless (the brave), Amity (the peaceful), and Erudite (the intelligent). On an appointed day of every year, all sixteen-year-olds must select the faction to which they will devote the rest of their lives.', 7, 'https://m.media-amazon.com/images/I/91oNu+R7EUL._AC_UF894,1000_QL80_.jpg'),
('9780062024037', 'Insurgent', 'Dystopian/Young Adult', '2012-05-01', 14, '2024-03-11', 'As war surges in the factions of dystopian Chicago all truths are suspect. Trust no one. Tris has survived a brutal attack on her former home and family. But she has paid a terrible price. Wracked by grief and guilt she becomes ever more reckless as she struggles to accept her new future.', 7, 'https://images.booksense.com/images/046/024/9780062024046.jpg'),
('9780062024044', 'Allegiant', 'Dystopian/Young Adult', '2013-10-22', 14, '2024-03-11', 'The faction-based society that Tris Prior once believed in is shattered - fractured by violence and power struggles and scarred by loss and betrayal. So when offered a chance to explore the world past the limits she''s known, Tris is ready. Perhaps beyond the fence, she and Tobias will find a simple new life together, free from complicated lies, tangled loyalties, and painful memories.', 7, 'https://m.media-amazon.com/images/I/81DPjDhnE-L._AC_UF894,1000_QL80_.jpg'),
('9780439554930', 'Harry Potter and the Philosopher''s Stone', 'Fantasy/Fiction', '1997-06-26', 5, '2024-03-11', 'Harry Potter has never played a sport while flying on a broomstick. He''s never worn a cloak of invisibility, befriended a giant, or helped hatch a dragon. All Harry knows is a miserable life with the Dursleys, his horrible aunt and uncle, and their abominable son, Dudley.', 8, 'https://www.unitedcs.co.uk/wp-content/uploads/2018/11/hp-phil_stone.jpg'),
('9780439064873', 'Harry Potter and the Chamber of Secrets', 'Fantasy/Fiction', '1998-06-02', 5, '2024-03-11', 'Ever since Harry Potter had come home for the summer, the Dursleys had been so mean and hideous that all Harry wanted was to get back to the Hogwarts School for Witchcraft and Wizardry.', 8, 'https://m.media-amazon.com/images/I/818umIdoruL._AC_UF894,1000_QL80_.jpg'),
('9780439136358', 'Harry Potter and the Prisoner of Azkaban', 'Fantasy/Fiction', '1999-09-08', 5, '2024-03-11', 'Harry Potter is not a normal boy. He is a wizard. After a terrible childhood, he has finally been taken away from his horrible aunt and uncle thanks to Hagrid, the Keeper of Keys and Grounds at Hogwarts School of Witchcraft and Wizardry. Harry has a lot to learn about his identity and destiny, and his magical education begins at Hogwarts.', 8, 'https://m.media-amazon.com/images/I/51pBxR5u1HL.jpg');
""")

# This query will be executed and will populate the AuthorBook joining table with AuthorIDs and the respective BookIDs for books authored by that author. This table will allow for a book to have multiple authors, and one author to have multiple books.

cur.execute("""INSERT INTO AuthorBook (AuthorID, BookID) VALUES (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12), (13, 13), (14, 14), (14, 15), (14, 16), (15, 17), (15, 18), (15, 19);""")

# This query will be executed and will populate the BookCopy table with BookIDs, and where a book has multiple copies, multiple CopyIDs for that book. 

cur.execute("""
INSERT INTO BookCopy (CopyID, BookID, AccessionNumber) VALUES (1, 1, "T40376"), (2, 1, "T40376"), (1, 2, "T40379"), (1, 3, "T40388"), (1, 4, "T40360"), (1, 5, "T40403"), (1, 6, "T40619"), (1, 7, "T40635"), (2, 7, "T40635"), (1, 8, "T40376"), (1, 9, "T40380"), (1, 10, "T40400"), (1, 11, "T40450"), (1, 12, "T40560"), (1, 13, "T40423"), (1, 14, "T40560"), (2, 14, "T40560"), (1, 15, "T40560"), (2, 15, "T40560"), (1, 16, "T40560"), (2, 16, "T40560"), (1, 17, "T40560"), (1, 18, "T40560"), (1, 19, "T40560");    
""")

# This query will be executed and will populate the reader table with example reader information. Where readers are librarians an AdminCode value has been provided, otherwise it has been left NULL. Example salts and hashes have been used, just to provde the library with a corpus of readers to test funcitonality on.

cur.execute("""
    INSERT INTO Reader VALUES
    (1, 'John', 'Doe', 'john_doe', 'salt1', 'hash1', 'john.doe@example.com', 'john@gmail.com', '2005-08-15', 10, 'Wa3b', NULL),
    (2, 'Jane', 'Smith', 'jane_smith', 'salt2', 'hash2', 'jane.smith@example.com', 'jane@gmail.com', '2006-03-25', 9, 'Le2a', NULL),
    (3, 'Michael', 'Johnson', 'michael_johnson', 'salt3', 'hash3', 'michael.johnson@example.com', 'michael@gmail.com', '2004-11-10', 11, 'Le2a', NULL),
    (4, 'Emily', 'Williams', 'emily_williams', 'salt4', 'hash4', 'emily.williams@example.com', 'emily@gmail.com', '2003-09-20', 12, 'Le2a', NULL),
    (5, 'David', 'Brown', 'david_brown', 'salt5', 'hash5', 'david.brown@example.com', 'david@gmail.com', '2007-05-08', 8, 'Le2a', NULL),
    (6, 'Sarah', 'Jones', 'sarah_jones', 'salt6', 'hash6', 'sarah.jones@example.com', 'sarah@gmail.com', '2008-02-18', 7, 'Le2a', "57493"),
    (7, 'Matthew', 'Davis', 'matthew_davis', 'salt7', 'hash7', 'matthew.davis@example.com', 'matthew@gmail.com', '2009-07-12', 6, 'Le2a', "57493"),
    (8, 'Kate', 'Wood', 'kate_wood', 'salt3', 'hash3', 'kate.wood@example.com', 'kate@gmail.com', '2006-11-10', 11, 'Le2a', NULL),
    (9, 'Emily', 'Johnson', 'emily_johnson', 'salt8', 'hash8', 'emily.johnson@example.com', 'emily@gmail.com', '2005-10-12', 10, 'Wa3b', NULL),
    (10, 'Daniel', 'Brown', 'daniel_brown', 'salt9', 'hash9', 'daniel.brown@example.com', 'daniel@gmail.com', '2006-07-05', 9, 'Le2a', NULL),
    (11, 'Olivia', 'Martinez', 'olivia_martinez', 'salt10', 'hash10', 'olivia.martinez@example.com', 'olivia@gmail.com', '2004-12-28', 11, 'Le2a', NULL),
    (12, 'James', 'Anderson', 'james_anderson', 'salt11', 'hash11', 'james.anderson@example.com', 'james@gmail.com', '2003-09-15', 12, 'Le2a', NULL),
    (13, 'Sophia', 'Garcia', 'sophia_garcia', 'salt12', 'hash12', 'sophia.garcia@example.com', 'sophia@gmail.com', '2007-03-30', 8, 'Le2a', NULL);
            """)

# This query will be executed and will populate the Review table with information.

cur.execute("""
    INSERT INTO Review (BookID, ReaderID, ReviewText, Rating, DateReviewed) VALUES 
    (1, 1, 'This is a great book! I loved the characters and the plot.', 5, "2020-06-19"),
    (1, 5, 'This is a great book! Darcy and Elizabeth are so cute.', 5, "2017-03-14"),
    (2, 2, 'I love Scout!', 3, "2018-09-09"),
    (2, 3, 'To Kill a Mockingbird is a timeless classic. The story is powerful and the characters are unforgettable.', 5, "2016-05-13"),
    (3, 3, 'The Book Thief is a beautifully written and emotionally gripping novel. It provides a unique perspective on World War II.', 4, "2015-12-17"),
    (4, 4, 'One of Us Is Lying is a thrilling mystery with twists and turns that kept me guessing until the end.', 4, "2022-02-24"),
    (5, 5, 'A Court of Thorns and Roses is a captivating fantasy with rich world-building and complex characters.', 5, "2024-01-04"),
    (6, 6, 'The Catcher in the Rye is a thought-provoking novel that captures the angst and confusion of adolescence.', 4, "2023-07-27"),
    (7, 7, 'Jane Eyre is a timeless classic that explores themes of love, independence, and social class.', 3, "2016-09-12"),
    (1, 3, 'A classic that never gets old. Loved every page!', 5, '2023-01-15'),
    (1, 4, 'Pride and Prejudice is a masterpiece of English literature.', 5, '2023-02-05'),
    (1, 7, 'One of the best romance novels ever written.', 5, '2023-02-10'),
    (1, 6, 'Enjoyed reading Pride and Prejudice. The characters are memorable and the writing is excellent.', 4, '2023-02-18');
          
            """)

# This query will be executed and will populate the Loan table with information on library loans.

cur.execute(
"""INSERT INTO Loan (CopyID, BookID, ReaderID, LoanStartDate, LoanEndDate, LoanStatus)
VALUES
    (1, 1, 3, '2024-02-20', '2024-03-05', 'Ended'), 
    (1, 4, 3, '2024-02-20', '2024-03-05', 'Ended'),
    (2, 1, 2, '2024-02-26', '2024-03-11', 'Ended'),
    (1, 2, 1, '2024-02-15', '2024-02-29', 'Ended'), 
    (1, 3, 5, '2024-02-12', '2024-02-26', 'Ended'), 
    (1, 4, 4, '2024-02-04', '2024-02-18', 'Ended'), 
    (1, 5, 6, '2024-02-18', '2024-03-03', 'Ended'),
    (1, 7, 3, '2024-02-10', '2024-02-24', 'Ended'),
    (2, 7, 4, '2024-02-13', '2024-02-27', 'Ended'),
    (1, 6, 8, '2024-02-13', '2024-02-27', 'Ended'),
    (1, 4, 8, '2024-02-13', '2024-02-27', 'Ended'), 
    (1, 3, 1, '2024-01-10', '2024-01-24', 'Ended'),
    (1, 2, 2, '2024-01-15', '2024-01-29', 'Ended'),
    (1, 4, 3, '2024-01-20', '2024-02-03', 'Ended'),
    (1, 5, 4, '2024-01-25', '2024-02-08', 'Ended'),
    (1, 6, 5, '2024-01-30', '2024-02-13', 'Ended'),
    (1, 7, 6, '2024-02-05', '2024-02-19', 'Ended'),
    (1, 8, 7, '2024-02-10', '2024-02-24', 'Ended'),
    (1, 9, 8, '2024-02-15', '2024-03-01', 'Ended'),
    (1, 10, 9, '2024-02-20', '2024-03-05', 'Ended'),
    (1, 11, 10, '2024-02-25', '2024-03-10', 'Ended'),
    (1, 12, 11, '2024-03-01', '2024-03-15', 'Ended'),
    (1, 13, 12, '2024-03-06', '2024-03-20', 'Ended'),
    (1, 17, 3, '2024-02-26', '2024-03-10', 'Active'),
    (1, 14, 5, '2024-03-07', '2024-03-23', 'Active');"""                  
            )

# This query will check if there is a loan for a given book's copy that has a current status of 'Active', i.e. the book copy is out of the library, and if so will update the associated BookCopy's Status to 'On Loan', otherwise it will be 'Available'.


cur.execute("""
UPDATE BookCopy
SET Status = 
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM Loan
            WHERE Loan.CopyID = BookCopy.CopyID AND Loan.BookID = BookCopy.BookID
            AND Loan.LoanStatus = 'Active'
        ) THEN 'On Loan'
        ELSE 'Available'
    END;                
            """)

# This query will be executed and will populate the ReadingList table with readers' reading lists.

cur.execute("""
INSERT INTO ReadingList (ReaderID, ReadingListTitle) VALUES 
(1, 'Books For English A-Level'),
(1, 'Want-to-Read'),
(2, 'Read in the Summer'),
(3, 'Recommended to me'),
(6, 'Fantasy'), 
(7, 'Austen Vibes'),
(7, 'Favourites');
            """)

# This query will be executed and will populate the ReadingListBook table, with information about which books are in which reading list, and will allow for reading lists to contain multiple books, and for book to be in multiple reading lists.

cur.execute("""
INSERT INTO ReadingListBook (ReadingListID, BookID, Read)VALUES
(1, 1, 1),
(1, 6, 0),
(1, 7, 0),
(2, 3, 0),
(2, 4, 0),
(3, 5, 0),
(4, 1, 1),
(4, 2, 1),
(5, 5, 0),
(6, 1, 1),
(6, 7, 0),
(7, 3, 1),
(7, 4, 1),
(7, 5, 1);           
            """)

# This query will be executed and will populate the Reservation table with information about reservations.

cur.execute("""INSERT INTO Reservation (CopyID, BookID, ReaderID, ReservationStatus, QueuePosition, Priority) 
VALUES
    (1, 1, 2, 'Fulfilled', 2, 1),
    (1, 1, 6, 'Fulfilled', 3, 2),
    (1, 1, 5, 'Fulfilled', 4, 2),
    (1, 2, 4, 'Fulfilled', 1, 2);
    """)  

# This statement will commit all the previous transactions to the database, so that changes such as the newly created tables, and inserted information will be permanently saved. 
con.commit()
# This command will close the database connection to 'library.db'.
con.close()