import string
import random
import numpy as np
class YourHashingAlgorithm:
    # Your other functions here...

    # Recursive function to perform arithmetic operations on string chunks
    def processChunks(self, chunks):
        # Base case: if there's only one chunk left, return its numerical value
        if len(chunks) == 1:
            return sum(ord(char) for char in chunks[0])
        else:
            # Recursive step: split the list of chunks into two halves
            mid = len(chunks) // 2
            left_sum = self.processChunks(chunks[:mid])
            right_sum = self.processChunks(chunks[mid:])
            # Combine the results of the recursive calls using some arithmetic operation
            return (left_sum * right_sum) % 1000000  # Example: multiply and take modulo

    # Modified function to generate chunks using recursion and perform arithmetic operations
    def getHash(self, password, salt):
        # Concatenate password and salt
        password = password + salt
        # Pad the concatenated string with "0" until its length is a multiple of 4
        while len(password) % 4 != 0: 
            password += "0"
        # Split the concatenated string into 4-character chunks
        chunks = [password[i:i+4] for i in range(0, len(password), 4)]
        # Process the chunks recursively using arithmetic operations
        hash_value = self.processChunks(chunks)
        # Map the hash value to the desired range (1-2000)
        return 1 + (hash_value % 2000)

username="pgtips"
password = "P1214vfva"
BINKEY = "000101001100"

    
def getChunks(password, salt):
    password = password + salt
    while len(password) % 4 != 0: 
        password += "0"
    
    chars = []
    for char in password:
        chars.append(ord(char))
    chunks = [chars[i:i+4] for i in range(0, len(chars)-3, 4)]
    return chunks

def getBinaryChunks(chunks):
    binaryChunks = []
    for chunk in chunks:
        binaryChunk = "{0:012b}".format(np.sum(chunk))
        binaryChunks.append(binaryChunk)
    return binaryChunks

def getXORChunks(binaryChunks, binkey):
    xorChunks = []
    for chunk in binaryChunks:
        xorChunks.append(int(chunk, 2) ^ int(binkey, 2))
    return xorChunks

def processChunks(chunks):
    if len(chunks) == 1:
        return sum(chunks)
    else:
        mid = len(chunks) // 2
        left_sum = processChunks(chunks[:mid])
        right_sum = processChunks(chunks[mid:])
        return (left_sum * right_sum) % 1000000 

def getSalt(username):
        length = len(username)
        characters = string.ascii_letters + string.digits + string.punctuation
        salt = "".join(random.choice(characters) for i in range(length))
        return salt
    
def getHash(password, salt, key):
    chunks = getChunks(password, salt)
    binaryChunks = getBinaryChunks(chunks)
    xorChunks = getXORChunks(binaryChunks, key)
    hash = processChunks(xorChunks)
    return hash % 1000

salt = getSalt(username)
print(salt)
print(getHash(password, salt, BINKEY))
    



    # Method to sort the array using a merge sort algorithm
    # def mergeSort(self, arr):
    #     if len(arr) > 1:
    #         mid = len(arr) // 2
    #         leftHalf = arr[:mid]
    #         rightHalf = arr[mid:]

    #         self.mergeSort(leftHalf)
    #         self.mergeSort(rightHalf)

    #         i = j = k = 0
    #         while i < len(leftHalf) and j < len(rightHalf):
    #             if leftHalf[i] < rightHalf[j]:
    #                 arr[k] = leftHalf[i]
    #                 i += 1
    #             else:
    #                 arr[k] = rightHalf[j]
    #                 j += 1
    #             k += 1

    #         while i < len(leftHalf):
    #             arr[k] = leftHalf[i]
    #             i += 1
    #             k += 1

    #         while j < len(rightHalf):
    #             arr[k] = rightHalf[j]
    #             j += 1
    #             k += 1
