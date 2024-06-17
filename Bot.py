from threading import Thread
import datetime
import numpy as np
import cv2 
import time
import os
from PIL import Image
import telebot
from telebot import types
import shutil
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


bot = telebot.TeleBot("7337674309:AAEfdZCAqFVW60XPJQRqs7m2_uhFlsSBfv8")

cascadePath = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath)

path = "./personality"
history_path="./historyphotos"
images = []
labels = []
names = []
persons=[]
pause = False
recognizer = None

superadmin_id = 727141791
admins_id=[superadmin_id]
password ="2031"

def get_images(path):
    images = []
    labels = []
    names = []
    i=0
    # распечатать все файлы и папки рекурсивно
    for dirpath, dirnames, filenames in os.walk(path):
        # перебрать каталоги
        for dirname in dirnames:
            print("Каталог:", os.path.join(dirpath, dirname))
            path2 = os.path.join(dirpath, dirname)
            # перебрать файлы
            names.append(dirname)
            for filename in os.listdir(path2):
                print("Файл:", os.path.join(path2, filename))
                gray = Image.open(os.path.join(path2, filename)).convert('L')
                image = np.array(gray, 'uint8')
                images.append(image)
                labels.append(i)    
            i+=1
        
    return images, labels, names

def init():
    global images,labels,names,pause,recognizer
    pause = True
    time.sleep(1.5) # для того, чтобы поток успел выйти
    images,labels,names = get_images(path)
    print(len(images))
    recognizer =cv2.face.LBPHFaceRecognizer_create(1,8,8,8,123)
    recognizer.train(images, np.array(labels))
    pause = False

def threadCamFunc():
    global last_face, last_image, last_id, names,last_name,pause,recognizer
    last_recognized_name = ""
    while(cap.isOpened() and not pause):

        ret, frame = cap.read()             #получаем кадр из видеопотока
        if frame is None:                   #проверка на корректность кадра
            break

        last_image = frame

        #показываем кадр в opencv окне
        key = cv2.waitKey(1) & 0xFF
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = faceCascade.detectMultiScale(frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        src =  frame
    
        if len(faces) > 0 :
            for (x, y, w, h) in faces:            
                crop_frame = frame[y:y+h, x:x+w]
                number_predicted, conf = recognizer.predict(crop_frame)
                last_face = crop_frame
                last_id =str(number_predicted) +": " + str(int(conf))
                last_name = names[number_predicted]

                if(last_recognized_name!=last_name):
                    if(conf<=60):
                        bot.send_message(superadmin_id, "Распознан " + last_name)
                    else:
                        bot.send_message(superadmin_id, "Похож на " + last_name)                
                    last_recognized_name = last_name
                
    time.sleep(1)

init()
cap = cv2.VideoCapture(0)

last_face = None 
last_image = None 
last_id = -1
last_name = None
threadCam =Thread(target=threadCamFunc)
threadCam.daemon = True
threadCam.start()

def id_in_admins(message):
    return message.from_user.id in admins_id
def send_commands(message):
    bot.send_message(message.from_user.id, "Привет")
    bot.send_message(message.from_user.id, "Список моих команд")
    markup = types.ReplyKeyboardMarkup()
    item1 = types.KeyboardButton('Привет')
    item2 = types.KeyboardButton('Последний')
    item3 = types.KeyboardButton('Фото')
    markup.add(item1,item2,item3)
    bot.send_message(message.chat.id, "Запомни (Имя)", reply_markup=markup)
    bot.send_message(message.chat.id, "Показать (Имя)", reply_markup=markup)
    bot.send_message(message.chat.id, "Удалить (Имя)", reply_markup=markup)


@bot.message_handler(commands=['hi'])
def process_hi1_command(message: types.Message):
    bot.send_message(message.chat.id, "Hi!")

@bot.message_handler(content_types=["text"])
def handler_text(message):
    global labels,names,images
    text  = message.text.split()
    if message.text == "/start":
       send_commands(message)
    elif str(message.text).lower() == "фото" and id_in_admins(message):
        # Делаем снимок
        bot.send_message(message.from_user.id, "Снимаю")
        cv2.imwrite('cam.png', last_image)
        file = open('cam.png', 'rb')
        bot.send_photo(message.from_user.id, file)

    elif str(text[0]).lower()=="запомни" and len(text)==2 and id_in_admins(message):
        pathFace=text[1]
        if not os.path.isdir("./personality/"+pathFace):
            os.mkdir("./personality/"+pathFace)
        bot.send_message(message.from_user.id, "Запоминаю. "+pathFace+", смотрите в камеру 10 сек..")
        
        for i in range(0,10+1):
            if last_face is not None:
                fn = "./personality/temp.jpg"
                cv2.imwrite(fn,last_face)
                os.rename(fn, "./personality/"+pathFace+"/"+str(i)+".jpg")
            time.sleep(1)
        bot.send_message(message.from_user.id, "Готово.")
        bot.send_message(message.from_user.id, "Обучаюсь...")
        init()
        bot.send_message(message.from_user.id, "Готово")
    elif message.text == "Привет" or message.text == "привет":
        bot.send_message(message.from_user.id, str("Привет, ")+str(message.from_user.first_name))
    elif str(message.text).lower() == "последний" and id_in_admins(message):
        if not last_face is None:
            bot.send_message(message.from_user.id, "Последний был " + last_name)
            bot.send_message(message.from_user.id, "Отправляю фото..")
            cv2.imwrite('face.png', last_face)
            file = open('face.png', 'rb')
            bot.send_photo(message.from_user.id, file)
        else:
            bot.send_message(message.from_user.id, "Никто не занимал")
    elif str(text[0]).lower()=='админ':
        if len(text)>=2:
            if str(text[1])==password:
                if len(text)==2:
                    tmp_id = message.from_user.id
                elif len(text)==3:
                    tmp_id = text[3]
                if tmp_id in admins_id:
                    bot.send_message(message.from_user.id, "Пользователь уже администратор")
                else:
                    admins_id.append(tmp_id)
                    bot.send_message(message.from_user.id, "Пользователь добавлен в администраторы")
            else:
                bot.send_message(message.from_user.id, "Неправильный пароль")
        else:
            bot.send_message(message.from_user.id, "Неправильный синтаксис команды. Админ пароль (telegram_user_id def= message.user.id))")
    elif str(text[0]).lower()=='удалить' and len(text)==2 and id_in_admins(message):
        if os.path.isdir("./personality/"+str(text[1])):
            shutil.rmtree("./personality/"+str(text[1]))
            bot.send_message(message.from_user.id, "Удалено")
        else:
            bot.send_message(message.from_user.id, "Не найдено")
    elif str(text[0]).lower()=='показать' and id_in_admins(message):
        if os.path.isdir("./personality/"+str(text[1])):
            for file in os.listdir("./personality/"+str(text[1])):
                bot.send_message(message.from_user.id, file)
        else:
            bot.send_message(message.from_user.id, "Не найдено")
       
    else:
        pass
        bot.send_message(message.from_user.id, "Упс.. Что-то пошло не так. Возможно вы не являетесь администратором")
        send_commands(message)
bot.polling(none_stop=True, interval=0)