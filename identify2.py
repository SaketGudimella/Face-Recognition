#identity2.py
# Import necessary libraries

from ultralytics import YOLO
from ultralytics.engine.results import Results  
from deepface import DeepFace
from PIL import Image
import shutil
import os
import csv
from datetime import datetime

totalKnownFaces=0
totalUnknownFaces=0
knownNames =[]

def nameFormat(names):
    namesNew = []
    for name in names:
        newName = name.replace('.png', '').replace('.jpg', '').replace('_',' ').lower()
        namesNew.append(newName[:-1])
    return namesNew

# Example usage:
names = ["image1.jpg", "image2.jpg", "image3.jpg"]
formatted_names = nameFormat(names)
print(formatted_names)


def mark_present_in_csv(knownNames, subject_chosen):
    
    
    today_date = datetime.today().strftime('%d/%m/%Y')
    #get current directory
    current_directory = os.path.dirname(os.path.abspath(__file__))
    #construct file path to attendance.csv
    csv_file_path = os.path.join(current_directory, 'attendance', f'{subject_chosen}.csv')


    # Read the CSV file into a list of dictionaries
    with open(csv_file_path, 'r', newline='') as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    # Update the attendance status based on knownNames list
    for row in rows:
        # Extract name from the row
        csv_name = row['Name']
        
        # Remove underscores from the names for comparison
        csv_name_lower = csv_name.lower()
        # print(csv_name_lower)
        # knownNames_no_underscore = [nameFormat(name).lower() for name in knownNames]
        # for x in knownNames_no_underscore:
        #     print(x)
        knownNames_new = nameFormat(knownNames)
        
        
        # Check if the name in the CSV row is exactly in knownNames
        if csv_name_lower in knownNames_new:
            row[today_date] = 'P'  # Mark present under today's date
        else:
            row[today_date] = 'A'  # Mark absent under today's date


    header = reader.fieldnames + [today_date]   # Update the header with today's date

    # Write the updated rows back to the CSV file
    with open(csv_file_path, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

def faceRecognition(input_image, subject_chosen):

    global totalKnownFaces
    global totalUnknownFaces


    # Path to the directory containing cropped objects
    cropped_objects_dir = "./faces/"
    
    # Path to the directory to save unknown faces
    unknown_faces_dir = "./unknown/"
    
    # Path to the directory to save known faces
    known_faces_dir = "./known/"
    
    # Initialize a list to store the extracted names
    extracted_names = []
    
    # Check if the 'unknown' folder exists, otherwise create it
    if not os.path.exists(unknown_faces_dir):
        os.makedirs(unknown_faces_dir)
    else:
        # If the 'unknown' folder exists, clear all files and subfolders
        for file_or_folder in os.listdir(unknown_faces_dir):
            file_or_folder_path = os.path.join(unknown_faces_dir, file_or_folder)
            if os.path.isfile(file_or_folder_path):
                os.remove(file_or_folder_path)
            elif os.path.isdir(file_or_folder_path):
                shutil.rmtree(file_or_folder_path)

    # Check if the 'known' folder exists, otherwise create it
    if not os.path.exists(known_faces_dir):
        os.makedirs(known_faces_dir)
    else:
        # If the 'known' folder exists, clear all files and subfolders
        for file_or_folder in os.listdir(known_faces_dir):
            file_or_folder_path = os.path.join(known_faces_dir, file_or_folder)
            if os.path.isfile(file_or_folder_path):
                os.remove(file_or_folder_path)
            elif os.path.isdir(file_or_folder_path):
                shutil.rmtree(file_or_folder_path)
    
    # Iterate through the image files in the directory
    for filename in os.listdir(cropped_objects_dir):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            img_path = os.path.join(cropped_objects_dir, filename)
            model = DeepFace.find(img_path=img_path, db_path="database", enforce_detection=False, model_name="Facenet512")

            # print("Model length:", len(model))
            # print("Model:", model)


            # Check if a face was recognized in the image
            if model and len(model[0]['identity']) > 0:
                # Extract the name and append it to the list
                name = model[0]['identity'][0].split('/')[1]

                # name = model[0]['identity'][0].split('/')[0]
   

                print("Name:", name)

                # Save the known face into the 'known' folder
                known_faces_path = os.path.join(known_faces_dir, f"{name}.jpg")
                totalKnownFaces+=1
                knownNames.append(name)
                shutil.copy(img_path, known_faces_path)
                # mark as present in file
                # mark_present_in_csv(name)
            else:
                # If no face is recognized, set name to 'unknown'
                name = 'unknown'
                print("No face detected in:", img_path)
                # Save the unknown face into the 'unknown' folder
                unknown_faces_path = os.path.join(unknown_faces_dir, f"{totalUnknownFaces}.jpg")
                totalUnknownFaces+=1
                shutil.copy(img_path, unknown_faces_path)
                
            extracted_names.append(name)
    mark_present_in_csv(knownNames, subject_chosen)        
    return extracted_names

def getKnownName():
    return knownNames

def setKnownName():
    global knownNames
    knownNames=[]

def setFacesToZero():
    global totalKnownFaces
    global totalUnknownFaces
    totalKnownFaces=0
    totalUnknownFaces=0

def getKnownFaces():
    return totalKnownFaces

def getUnknownFaces():
    return totalUnknownFaces

def faceExtraction(input_image, model, results):
    # Load the image
    image = Image.open(input_image)
    detected_objects = []

    if hasattr(results, 'boxes') and hasattr(results, 'names'):
        for box in results.boxes.xyxy:
            object_id = int(box[-1])
            object_name = results.names.get(object_id)
            x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])

            detected_objects.append((object_name, (x1, y1, x2, y2)))

    # Create or clear the 'faces' directory
    if os.path.exists("./faces"):
        shutil.rmtree("./faces")
    os.makedirs("./faces")

    totalFaces=0
    # Crop and save each detected object
    for i, (object_name, (x1, y1, x2, y2)) in enumerate(detected_objects):
        object_image = image.crop((x1, y1, x2, y2))
        object_image.save(f"./faces/face{i}.jpg")
        totalFaces+=1
        
    return totalFaces



# def faceDetection(uploaded_file):
#     img = Image.open(uploaded_file)
#     temp_image_path = "./temp_image.jpg"  # Temporary path to store the converted image
#     img.save(temp_image_path, format="JPEG")

#     # Use the Ultralytics model
#     model = YOLO('best.pt')
#     results: Results = model.predict(temp_image_path)[0]

#     total_faces = faceExtraction(temp_image_path, model, results)
    
#     # Remove the temporary image file
#     os.remove(temp_image_path)

#     return total_faces


def faceDetection(uploaded_file):
    img = Image.open(uploaded_file)
    temp_image_path = "./temp_image.jpg"  # Temporary path to store the converted image
    img.save(temp_image_path, format="JPEG")

    # Delete database/representations_facenet512.pkl file if it exists
    # representations_file = os.path.join("database", "representations_facenet512.pkl")
    # if os.path.exists(representations_file):
    #     os.remove(representations_file)

    # Use the Ultralytics model
    model = YOLO('best.pt')
    results: Results = model.predict(temp_image_path)[0]

    total_faces = faceExtraction(temp_image_path, model, results)
    
    # Remove the temporary image file
    os.remove(temp_image_path)

    return total_faces
