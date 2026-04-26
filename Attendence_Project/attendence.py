# =====================================
# FINAL FACE ATTENDANCE SYSTEM 
# =====================================

import cv2
import numpy as np
import os
import serial
import time
from datetime import datetime


# ================= LOGIN SCREEN =================

def login_screen():

    while True:

        img = np.zeros((400,600,3),dtype=np.uint8)

        cv2.rectangle(img,(0,0),(600,80),(40,40,40),-1)

        cv2.putText(img,"ATTENDANCE LOGIN",
                    (150,50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,(0,255,255),2)

        cv2.putText(img,"Press ENTER to Start",
                    (160,180),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,(255,255,255),2)

        cv2.putText(img,"Press Q to Exit",
                    (190,230),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,(200,200,200),1)

        cv2.imshow("Login",img)

        key = cv2.waitKey(1)

        if key == 13:
            break

        if key & 0xFF == ord('q'):
            exit()

    cv2.destroyWindow("Login")


login_screen()


# ================= ESP =================

try:
    esp = serial.Serial("COM11",115200)
    time.sleep(2)
except:
    esp = None


# ================= LOAD + TRAIN MODEL =================

path = "images"
faces = []
labels = []
names = []
label_id = 0

face_detector = cv2.CascadeClassifier(cv2.data.haarcascades +
                                       "haarcascade_frontalface_default.xml")

for file in os.listdir(path):

    img_path = os.path.join(path,file)
    img = cv2.imread(img_path)

    if img is None:
        continue

    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    detected = face_detector.detectMultiScale(gray,1.3,5)

    for (x,y,w,h) in detected:
        faces.append(gray[y:y+h,x:x+w])
        labels.append(label_id)

    names.append(os.path.splitext(file)[0])
    label_id += 1


recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(faces,np.array(labels))

print("✅ MODEL READY")


# ================= REGISTER MODE =================

def register_face(cap):

    global names, recognizer

    name = input("Enter student name: ").lower()

    print("Look at camera...")

    while True:

        ret,frame = cap.read()
        gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

        faces_detected = face_detector.detectMultiScale(gray,1.3,5)

        for (x,y,w,h) in faces_detected:

            face_img = frame[y:y+h,x:x+w]
            cv2.imwrite(f"images/{name}.jpg",face_img)

            print("✅ Face saved!")

            # retrain model

            faces_data = []
            labels_data = []
            names.clear()

            label_id = 0

            for file in os.listdir("images"):

                img_path = os.path.join("images",file)
                img = cv2.imread(img_path)

                if img is None:
                    continue

                gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
                detected = face_detector.detectMultiScale(gray,1.3,5)

                for (x,y,w,h) in detected:
                    faces_data.append(gray[y:y+h,x:x+w])
                    labels_data.append(label_id)

                names.append(os.path.splitext(file)[0])
                label_id += 1

            recognizer.train(faces_data,np.array(labels_data))

            print("✅ Model Updated!")

            return

        cv2.imshow("Register Mode",frame)

        if cv2.waitKey(1)==13:
            break


# ================= ATTENDANCE =================

marked_names = []
unknown_faces = set()

def markAttendance(name):

    global marked_names

    if name in marked_names:
        return

    now = datetime.now()
    dateString = now.strftime("%d-%m-%Y")
    timeString = now.strftime("%H:%M:%S")

    if not os.path.exists("Attendance.csv"):
        with open("Attendance.csv","w") as f:
            f.write("NAME,DATE,TIME\n")

    with open("Attendance.csv","a") as f:
        f.write(f"{name},{dateString},{timeString}\n")

    marked_names.append(name)

    print(name,"ATTENDANCE MARKED")

    if esp:
        esp.write((name+"\n").encode())


# ================= CAMERA =================

cap = cv2.VideoCapture(0)

while True:

    success,img = cap.read()
    if not success:
        break

    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    faces_detected = face_detector.detectMultiScale(gray,1.3,5)


    # ================= MODERN UI =================

    blur = cv2.GaussianBlur(img,(15,15),0)
    img = cv2.addWeighted(img,1,blur,0.15,0)


    # TOP PANEL
    overlay = img.copy()
    cv2.rectangle(overlay,(0,0),(640,80),(20,20,20),-1)
    img = cv2.addWeighted(overlay,0.6,img,0.4,0)

    cv2.putText(img,"AUTOMATIC ATTENDANCE SYSTEM",
                (90,45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,(0,255,255),2)

    nowtime = datetime.now().strftime("%d-%m-%Y  %H:%M:%S")
    cv2.putText(img,nowtime,(210,70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,(220,220,220),1)


    # LEFT PANEL
    overlay = img.copy()
    cv2.rectangle(overlay,(10,90),(220,200),(30,30,30),-1)
    img = cv2.addWeighted(overlay,0.6,img,0.4,0)

    cv2.putText(img,"LIVE STATUS",(50,115),
                cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,255),2)

    cv2.putText(img,f"PRESENT : {len(marked_names)}",(25,150),
                cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)

    cv2.putText(img,f"UNKNOWN : {len(unknown_faces)}",(25,185),
                cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)


    # FACE LOOP
    for (x,y,w,h) in faces_detected:

        roi = gray[y:y+h,x:x+w]
        label,confidence = recognizer.predict(roi)

        if confidence < 70:

            name = names[label].upper()
            markAttendance(name)

            cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

            cv2.rectangle(img,(x,y+h),(x+w,y+h+45),(20,20,20),-1)

            cv2.putText(img,f"{name}",
                        (x+5,y+h+30),
                        cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)

        else:

            unknown_faces.add("U")

            cv2.rectangle(img,(x,y),(x+w,y+h),(0,0,255),2)
            cv2.putText(img,"UNKNOWN",
                        (x,y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)


    # FOOTER
    overlay = img.copy()
    cv2.rectangle(overlay,(0,440),(640,480),(20,20,20),-1)
    img = cv2.addWeighted(overlay,0.6,img,0.4,0)

    cv2.putText(img,"Press R to Register  |  Q to Exit",
                (170,470),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,(255,255,255),1)


    cv2.imshow("Webcam",img)

    key = cv2.waitKey(1)

    if key & 0xFF == ord('q'):
        break

    if key & 0xFF == ord('r'):
        register_face(cap)


cap.release()
cv2.destroyAllWindows()

if esp:
    esp.close()

os.startfile("Attendance.csv")
