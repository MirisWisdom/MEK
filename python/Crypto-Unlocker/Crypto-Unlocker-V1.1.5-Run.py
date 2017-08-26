'''
This program was written with the intent to fix damages done by incomplete cryptolocker decryptions.

A friend of the programmer's had his company hit by the virus and, even though they paid the ransom
some of their files were missed. This was because the drive letter mapping had changed between when
the files were encrypted and when they were decrypted. The programmer studied the virus extensively
within the bounds of his capability and wrote this program. I, the programmer, would like to remain
relatively anonymous so as to not become a potential target for the cryptolocker authors. Those bastards

There is no warrenty guranteed or implied through the use of this program. This program is written to NOT
overwrite the files it reads from, but just to be sure make sure that any files placed in the "Encrypted Files"
folder aren't your only copy of them in case something goes wrong

Again, there is no warrenty guranteed or implied and the use of this program is entirely of your own volition.
Using this program constitutes your agreement to not hold the author liable for any damages caused by it.

If you need reassurance of this program's function ask someone you know who programs to look over
it's code and verify it is not malicious.

Your friend, Mo


This program requires python to run. I'm not sure which version is required, but it was programmed and
has shown to work with python 3.3 so that should be the one to use.

Pycrypto is required for running this script. Download pycrypto installers downloaded from here:

https://github.com/appurify/appurify-python/tree/master/pycrypto



Update V1.1.1: Program is now able to use registry keys as the RSA key instead of only being able to use .bin
binary blobs. To do this export the private key from the registry as a .reg file and place it in the same
directory as Crypto-Unlocker-Run.py. You don't need to remove all the other entires from the .reg file, just
make sure the private key entry is in there.

Update V1.1.5: Added two checks to make sure the file being decrypted is actually encrypted.
If the file is not you will be alerted and the file will be skipped. There are 14 bytes of data that must
match if a file is to be considered encrypted to prevent accidentally decrypting something into garbage.
'''



import mmap
import struct
import os
import sys
import functools
import binascii

try:
    from Crypto.Cipher import AES
except:
    info = sys.version_info
    print("Error: PyCrypto not installed! PyCrypto is required for the program to run.")
    print("Please find and install PyCrypto for python v"+str(info[0])+"."+str(info[1])+"."+str(info[2]))
    input()
    sys.exit()

RSA_Key_File = 0

debug_print_mode = 0            #0 = regular printout   1 = debug printout
agreement_accepted = 0


if (agreement_accepted == 0):
    print('----------------------------')
    print('----PROGRAM WILL DECRYPT----')
    print('------ALL FILES IN THE------')
    print('---ENCRYPTED FILES FOLDER---')
    print('----------------------------')
    print()
    print('----------------------------')
    print('---A MESSAGE PRINTED HERE---')
    print('----WILL NOTIFY YOU WHEN----')
    print('---DECRYPTION IS FINISHED---')
    print('----------------------------')
    print()
    print()
    print("Do you accept the terms and conditions contained in the readme?")
    print("If you cannot find the readme they are also located in this file's header.")
    print("Decryption will start once you accept the agreement.")
    print()
    
    while not agreement_accepted:
        userinput = input("Type Yes to accept: ")
        if ( userinput.lower() == ("yes")):
            agreement_accepted = 1
        elif ( userinput.lower() == ("no")):
            agreement_accepted = -1
            print()
            print('You typed "No". The program will now close')
            input()
        else:
            print()
            print('You did not type "Yes"')
            print()




def Convert_Main():

    Current_Directory = []

    Encrypted_Files_Paths = []
    Decrypted_Files_Paths = []
    Decrypted_File_Headers_Paths = []
    Decrypted_File_AES_Keys_Paths = []

    Private_Key_N = 0
    Private_Key_d = 0


    encrypted_dir =(os.path.join(Current_Directory, 'Encrypted Files'))

    #returns the current directory so we can work from it
    Current_Directory = os.path.abspath(os.curdir)

    #Returns a list of all files contained in the "Encrypted Files" folder
    for root, directories, files in os.walk(encrypted_dir):
        for filename in files:
            # Join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            filepath.split(encrypted_dir, 1)
            Encrypted_Files_Paths.append(filepath)  # Add it to the list.

    #makes a copy of the encrypted files list and saves it as "Decrypted_Files_Paths"
    Decrypted_Files_Paths = list(Encrypted_Files_Paths)

    #makes a copy of the encrypted files list and saves it as "Decrypted_AES_Keys_Paths"
    Decrypted_File_AES_Keys_Paths = list(Encrypted_Files_Paths)

    
    
    #since the copied list still says "Encrypted Files" and we need it to
    #say "Decrypted Files" we need to change that in each string
    for file in range(0, len(Decrypted_Files_Paths)):
        Decrypted_Files_Paths[file] = Decrypted_Files_Paths[file].replace("Encrypted Files\\", "Decrypted Files\\")
        
    #since the copied list still says "Encrypted Files" and we need it to
    #say "AES Keys" we need to change that in each string
    for file in range(0, len(Decrypted_File_AES_Keys_Paths)):
        Decrypted_File_AES_Keys_Paths[file] = Decrypted_File_AES_Keys_Paths[file].replace("Encrypted Files\\", "AES Keys\\")
        Decrypted_File_AES_Keys_Paths[file] += ".aeskey"

    #makes a copy of the AES Key files list and saves it as "Decrypted_File_Headers_Paths"
    Decrypted_File_Headers_Paths = list(Decrypted_File_AES_Keys_Paths)

    #change the file extension on the new files
    for file in range(0, len(Decrypted_File_Headers_Paths)):
        Decrypted_File_Headers_Paths[file] = Decrypted_File_Headers_Paths[file].replace("AES Keys\\", "AES Keys\\Headers\\")
        Decrypted_File_Headers_Paths[file] = Decrypted_File_Headers_Paths[file].replace(".aeskey", ".header")


    for folder_list in (Decrypted_Files_Paths, Decrypted_File_AES_Keys_Paths, Decrypted_File_Headers_Paths):
        for folder in folder_list:
            if (not os.path.exists(os.path.dirname(folder))):
                os.makedirs(os.path.dirname(folder))

    Private_Key_Data = 0
    Checked_Root_Folder = 0
    RSA_Key_Format = 0#if the key is found in a bin file this is 0, if it's found in a reg file it's 1


    #the bytes below translate to "hex:07,02,00,00,00,a4,00,00,"
    #yea i know it's a lot. I didn't enjoy typing it all out either but it's the easiest method I can find.
    Registry_Private_Key_Start = [104,101,120,58,48,55,44,48,50,44,48,48,44,48,48,44,48,48,44,97,52,44,48,
                                  48,44,48,48,44,53,50,44,53,51,44,52,49,44,51,50,44,48,48,44,48,56,44,48,
                                  48,44,48,48,44,48,49,44,48,48,44,48,49,44,48,48,44,92,13,10,32,32]

    #now since the registry key data has friggen 0x00 padding between each byte
    #we need to add that in after each entry. Glad I could automate this >_>

    temp_int = len(Registry_Private_Key_Start)
    index = 0

    while index <= temp_int:
        Registry_Private_Key_Start.insert(index, 0)
        index += 2
        temp_int += 1

    #and now convert it to bytes so it can be used for searching
    Registry_Private_Key_Start = bytes(Registry_Private_Key_Start)

    #we'll be using this dictionary for easy integer conversion since, again, I don't know an easier way
    plaintext_to_int = {48:0, 49:1, 50:2, 51:3, 52:4, 53:5, 54:6, 55:7, 56:8, 57:9, 97:10, 98:11, 99:12, 100:13, 101:14, 102:15}
    

    if (debug_print_mode):
        print('---------------------------')
        print('--------DEBUG  MODE--------')
        print('---------------------------')
        print()
    
        
    #Checks for the private key

    
    for root, dirs, files in os.walk(Current_Directory):
        if (Checked_Root_Folder == 0):
            #make sure we only check the root folder since it gets more complicated otherwise
            Checked_Root_Folder = 1
            
            for Current_File in files:
                #Checks the file contains the string RSA2 starting at byte 9 to verify this is the private key

                Potential_Private_key = open(Current_File, 'rb')
                Potential_Private_Key_Data = mmap.mmap(Potential_Private_key.fileno(), 0, access=mmap.ACCESS_READ)

                try:#if we don't have this error handeler we might end up trying to seek in a file that's too small and crashing the program
                    Potential_Private_Key_Data.seek(8, 0)
                    Private_Key_ID_Tag = Potential_Private_Key_Data.read(4)
                    Private_Key_ID_Tag = (struct.unpack('>I', Private_Key_ID_Tag))[0]
                    
                    #translated from bytes, RSA2 becomes the unsigned integer 1381187890 so that's what we'll compare
                    if ( Private_Key_ID_Tag == 1381187890 ):
                        Private_Key_Data = Potential_Private_Key_Data
                        if (debug_print_mode):
                            print('---------------------------')
                            print("Private Key Found as file: ", Current_File)
                            print('---------------------------')
                        RSA_Key_File = Potential_Private_key
                        break

                    #if the file wasn't an RSA blob we check if it's a registry key
                    if ( Current_File.endswith('.reg') or Current_File.endswith('.REG') or Current_File.endswith('.Reg') ):
                        Potential_Private_Key_Data.seek(0,0)
                        registry_read_offset = Potential_Private_Key_Data.find(Registry_Private_Key_Start)

                        #if we have found the header of the private key we know this is where to start reading
                        if (registry_read_offset >= 0):
                            Private_Key_Data = Potential_Private_Key_Data
                            registry_read_offset += len(Registry_Private_Key_Start) - 1
                            
                            RSA_Key_Format = 1
                            if (debug_print_mode):
                                print('---------------------------')
                                print("Private Key Found as file: ", Current_File)
                                print('---------------------------')
                            RSA_Key_File = Potential_Private_key
                            break
                except ValueError:
                    pass
                Potential_Private_key.close()

    #If we can't find the private key we tell you we can't and we stop the program
    if (Private_Key_Data == 0):
        print ('----------------------------')
        print ('Private Key not found!!!')
        print ('Remember to place the private key in the root of Crypto-Unlocker')
        print ('That means the folder containing Crypto-Unlocker-Run.py')
        print ('----------------------------')
        print ('----Press Enter to Close----')
        print ('----------------------------')
        return()

    #parse and extract the actual key data into the modulus and exponent we need
    
    #if we found the private key in a bin file
    if (RSA_Key_Format == 0):
        Private_Key_Data.seek(20, 0)#move to the start of the RSA key data

        #now lets extract the actual numbers "N" and "d" from the byte data
        Private_Key_N = int.from_bytes(Private_Key_Data.read(256),'little')
        #since we only need the modulus(N) and the private exponent (d) we can skip the majority of this data
        Private_Key_Data.seek((128*5), 1)
        Private_Key_d = int.from_bytes(Private_Key_Data.read(256) ,'little')
    else:#if we found the private key in a registry file
        Private_Key_Data.seek(registry_read_offset, 0)#skip to the start of the modulus
        #do this twice to save code space
        for Donut in range(0, 2):
            deformatted_bytes = bytes()

            #do this for each byte in the key
            for Arby in range(0, 256):
                deformatted_byte = 0

                #do this for each hex character
                for Sigma in range(0, 2):
                    Private_Key_Data.seek(1, 1)#skip past the padding character

                    #convert the plaintext byte into it's equivelant hex representation
                    formatted_byte = (struct.unpack('B', Private_Key_Data.read(1)))[0]
                    
                    #if we enconuter a slash we skip past it and read the next byte
                    if (formatted_byte == 92):
                        Private_Key_Data.seek(9, 1)#skip past the padding characters
                        formatted_byte = (struct.unpack('B', Private_Key_Data.read(1)))[0]

                    formatted_byte = plaintext_to_int.get(formatted_byte)

                    #multiply the result by 16 if it's the first hex character
                    deformatted_byte += (formatted_byte * pow(16, (1 - Sigma)))

                #skip the comma and it's padding in the registry file unless this is the last byte being read
                if (Arby < 255 or Donut == 0):
                    Private_Key_Data.seek(2, 1)

                deformatted_bytes = b''.join([deformatted_bytes, (deformatted_byte.to_bytes(1, byteorder='big'))])
                
            if (Donut == 0):
                Private_Key_N = int.from_bytes(deformatted_bytes,'little')
                
                #skip past the other key components to the exponent
                Private_Key_Data.seek((128 * 5 * 6), 1)

                #since there are some extra characters such as the / we need to skip a little more
                Private_Key_Data.seek((25 * 10), 1)
            else:
                Private_Key_d = int.from_bytes(deformatted_bytes,'little')
    

    if (debug_print_mode):
        print("RSA key modulus:")
        print(Private_Key_N)
        print('---------------------------')

        print("RSA key private exponent:")
        print(Private_Key_d)
        print('---------------------------')

    #close the private key
    RSA_Key_File.close()
    
    #if we've found the private key file we can start decrypting the files
    for File_To_Convert in range(0, len(Encrypted_Files_Paths)):

        #open the encrypted file to convert and create the new decrypted files
        encrypted_file = open(Encrypted_Files_Paths[File_To_Convert], 'rb')
        decrypted_file_AES_key = open(Decrypted_File_AES_Keys_Paths[File_To_Convert], 'w+b')
        decrypted_file_Header = open(Decrypted_File_Headers_Paths[File_To_Convert], 'w+b')
        
        decrypted_file = open(Decrypted_Files_Paths[File_To_Convert], 'w+b')
        Encrypted_File_Data = mmap.mmap(encrypted_file.fileno(), 0, access=mmap.ACCESS_READ)

        File_Header = Encrypted_File_Data.read(20)
        Encrypted_AES_Key = Encrypted_File_Data.read(256)

        #save and close the header file
        decrypted_file_Header.write(File_Header)
        decrypted_file_Header.close()

        base = int.from_bytes(Encrypted_AES_Key,'little')

        Decrypted_AES_Key = (pow(base, Private_Key_d, Private_Key_N))
        Decrypted_AES_Key_Bytes = (Decrypted_AES_Key.to_bytes(256, byteorder='big'))

        #now we do a few IMPORTANT checks for certain expected data sequences in the decrypted
        #AES key data block which should pretty much completely prevent any fluke decryptions
        if ( ((Decrypted_AES_Key_Bytes[:2]) == b'\x00\x02') and ((Decrypted_AES_Key_Bytes[211:224]) == b'\x00\x08\x02\x00\x00\x10f\x00\x00\x20\x00\x00\x00') ):
 
            #convert the decrypted integer back to bytes and write to a key file
            Decrypted_AES_Key_Bytes = Decrypted_AES_Key_Bytes[212:]#byte order must be reversed when written to file so we use big
            #write the decrypted AES key for debug
            decrypted_file_AES_key.write(Decrypted_AES_Key_Bytes)#write the AES key to the file
            decrypted_file_AES_key.close()#close since we're done writing to it

            Decrypted_AES_Key_Bytes = Decrypted_AES_Key_Bytes[12:]

            #now that we've got the AES Key we can use it to decrypt the actual file data
            #since this will be a good chunk of code itself we're putting it in another function

            encrypted_file.seek(276, 0)

            cipher = AES.new(Decrypted_AES_Key_Bytes, AES.MODE_CBC, ('\x00'*16) )
            decrypted_data = encrypted_file.read()

            if ( (len(decrypted_data) % 16) == 0):
                #remove padding and write to file
                decrypted_data = cipher.decrypt(decrypted_data)
                decrypted_file.write(decrypted_data[:(len(decrypted_data) - (decrypted_data[len(decrypted_data)-1]))])

                print('Finished Decrypting:', Encrypted_Files_Paths[File_To_Convert])

                decrypted_file.close()
            else:
                print('---------------------------')
                print('Error Decrypting:', Encrypted_Files_Paths[File_To_Convert])
                print("Skipping above file as the encrypted data isn't a multiple of 16")
                print('---------------------------')
                decrypted_file.close()
                os.remove(Decrypted_Files_Paths[File_To_Convert])
                os.remove(Decrypted_File_AES_Keys_Paths[File_To_Convert])
                os.remove(Decrypted_File_Headers_Paths[File_To_Convert])

            encrypted_file.close()
        else:
            print('Skipping:', Encrypted_Files_Paths[File_To_Convert], "as it isn't encrypted")
            print('---------------------------')
            decrypted_file.close()
            decrypted_file_AES_key.close()
            os.remove(Decrypted_Files_Paths[File_To_Convert])
            os.remove(Decrypted_File_AES_Keys_Paths[File_To_Convert])
            os.remove(Decrypted_File_Headers_Paths[File_To_Convert])
    print()
    print('----------------------------')
    print('----DECRYPTION  FINISHED----')
    print('----------------------------')
    print()
    print('----------------------------')
    print('----Press Enter to Close----')
    print('----------------------------')

    return()


if(agreement_accepted > 0):
    #run main decryption process
    Convert_Main()
    #wait till enter is pressed to close command window when done decrypting
    input()
