
import os
import sys

if len(sys.argv) != 3:
    print('Invalid number of arguments\nUsage: python ffmpeg-flac_to_wav <folder of flac files, relative to place of execution> <output folder, relative to place of execution>\n------------------')


PATH = os.getcwd()

INPUT_FOLDER = os.path.join(PATH,sys.argv[1])
OUTPUT_FOLDER = os.path.join(PATH, sys.argv[2])

if (not os.path.exists(OUTPUT_FOLDER)):
    os.makedirs(OUTPUT_FOLDER)


files_to_convert = []
for root, directories, file in os.walk(INPUT_FOLDER):
   for file in file:
        if(file.endswith(".flac")):
            file_name = os.path.splitext(file)[0] + ".wav"
            print("'" + os.path.join(root,file_name) + "'")
            os.system("ffmpeg -i "+ "\'" + os.path.join(root,file) + "\' \'"  + os.path.join(OUTPUT_FOLDER, file_name) + "\'")


