import numpy as np
import streamlit as st
import os.path, time, datetime, random, json, pickle, spacy, nltk, pyttsx3, os, wave, shutil
import speech_recognition as sr
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import load_model
from pydub import AudioSegment

def spacy_entity(speech_text, dic):
    """
    extract the entities from the converted text
    """
    NER = spacy.load("spacy-entity/training/model-best")                    #load the custom trained model
    txt = NER(speech_text)                                                  #entity recognized from text
    for w in txt.ents:                                                      #loading all entities in dic
        dic[w.label_] = w.text

    return dic

def upload(raw_file, file_name):
    """
    upload audio and extract entities from it
    """
    start_time = time.time()
    dic = {}
    if raw_file is None:                                                                # check if file uploaded
        st.warning("Upload a file first!")
        return 0

    else:
        if raw_file is not None:
            if not os.path.isdir('saved-audio-upload'):                                             # create folder
                os.makedirs("saved-audio-upload")
                                
            sound = AudioSegment.from_file(raw_file)
            sound.export(f"saved-audio-upload/upload-{file_name}.wav", format="wav")
            file_path = f"saved-audio-upload/upload-{file_name}.wav"

            with sr.AudioFile(file_path) as source:
                audio_text = r.record(source)
                
                try:
                    text = r.recognize_google(audio_text)
                    st.success("text: " + text)
                
                except:
                    text = " "
                    st.write('Sorry.. run again...')

            upload_entity = spacy_entity(text, dic)                                        # entity extraction function called
            end_time = round(time.time() - start_time, 2)
            
            return upload_entity, end_time                                                  # returns entities extracted

def microphone(logtxtbox, logtxt):
    """
    input through microphone
    """
    try:
        with sr.Microphone() as source:                                         # use microphone
            r.adjust_for_ambient_noise(source, duration=0.2)                    # adjust noise

            logtxt += 'listening...\n'
            logtxtbox.text_area("CHATBOT", logtxt, height=300)

            audio = r.listen(source)                                            # listens thru mic
            return audio                                                        # returns audio

    except:
        return 0
        
def recognize(speech):
    """
    recognize the microphone input using google speech recognition
    """
    try:
        audio_text = r.recognize_google(speech)                             # speech to text
        return audio_text                                                   # returns text

    except:
        return 0                                                            # in case it doesn't recognizes text from speech and asks user to speak again

def audio_file(speech, file_name):
    """
    save the microphone input
    """

    with open(os.path.join("saved-audio", f'rec-{datetime.datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")}.wav'),"wb") as a:       #save audio in the folder 
        a.write(speech.get_wav_data())
        a.seek(0)

def one_audio():
    if not os.path.isdir('final-saved-audio'):
        os.makedirs("final-saved-audio")

    a = os.listdir("saved-audio")
    l = len(a)
    path = os.getcwd()

    os.chdir(f"{path}\\saved-audio")

    for i in range(l):   
        if i == 0:
            sound1 = AudioSegment.from_wav(a[i])
            continue
        else:
            sound2 = AudioSegment.from_wav(a[i])
            combined_sounds = sound1 + sound2
            sound1 = combined_sounds

    os.chdir(f'{path}')
    os.chdir(f"{path}\\final-saved-audio")
    combined_sounds.export(f'rec-{datetime.datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")}.wav', format="wav")
    os.chdir(f'{path}')
    shutil.rmtree("saved-audio")

def text_file(logtxt, file_name):
    """
    save the chat
    """
    if not os.path.isdir('saved-text'):                                             # create text folder
        os.makedirs("saved-text")
                                                                            
    try:
        if str is bytes: 
            result = u"{}".format(logtxt).encode("utf-8")
        else: 
            result = "{}".format(logtxt)

        with open(os.path.join("saved-text", f'text-{file_name}.txt'),"a") as t: 
            t.write(result)

    except sr.UnknownValueError:
        print("")
    except sr.RequestError as e:
        print("{0}".format(e))
    except KeyboardInterrupt:
        pass

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word) for word in sentence_words]
    return sentence_words

def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1
    return np.array(bag)

def predict_class(sentence):                                                        # predicts the most probable answer
        bow = bag_of_words(sentence)
        res = model.predict(np.array([bow]))[0]
        ERROR_THRESHOLD = 0.25   
        results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]

        results.sort(key=lambda x: x[1], reverse=True)
        return_list = []
        for r in results:
            return_list.append({'intent': classes[r[0]], 'probability': str(r[1])})
        return return_list

def get_response(intents_list, intents_json):                                       # generates response
    tag = intents_list[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if i['tag'] == tag:
            result = random.choice(i['responses'])
            break
    return result, tag

def speak_text(logtxt):                                                             # text to speech

    if not os.path.isdir('saved-audio'):                                            # create audio folder
        os.makedirs("saved-audio")

    engine = pyttsx3.init()                                                         # Initialize the engine
    engine.say(logtxt)
    engine.save_to_file(logtxt, f'saved-audio\\rec-{datetime.datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")}.wav')
    engine.runAndWait()

def chatbot(file_name):
    start_time = time.time()
    logtxtbox = st.empty()
    logtxt = 'Hello, hope you\'re doing good. Want to book a ride or update account details?\n'
    logtxtbox.text_area("CHATBOT", logtxt, height=300)
    speak_text(logtxt)

    dic = {
    "DROP_LOC": None,
    "PICKUP_LOC": None,
    "TIME": None}

    while (True):                                                               # chatbot initializes
        speech = microphone(logtxtbox, logtxt)                                  # microphone function
        if speech == 0:
            st.warning ('Microphone not working. Please check')
            break

        audio_file(speech, file_name)

        speech_text = recognize(speech)                                         # speech to text
        if speech_text == 0:
            logtxt += 'Sorry, i did not get that...\n'
            logtxtbox.text_area("CHATBOT", logtxt, height=300)
            speak_text("Sorry, i didn't get that")
            continue
        logtxt += speech_text+'\n'
        logtxtbox.text_area("CHATBOT", logtxt, height=300)

        ints = predict_class(speech_text)                                       # predicts probable answer
        res, use_tag = get_response(ints, intents)

        if use_tag == "drop_time_pickup" or use_tag == "drop_location" or use_tag == "time" or use_tag == "pickup_location":
            dic = spacy_entity(speech_text, dic)                                    

        if (use_tag == "drop_location" and dic["DROP_LOC"] == None):
            logtxt += 'Sorry didn\'t got your drop location. Try again\n'
            logtxtbox.text_area("CHATBOT", logtxt, height=300)
            speak_text('Sorry didn\'t got your drop location. Try again')
            continue

        if (use_tag == "time" and dic["TIME"] == None):
            logtxt += 'Sorry at what time?\n'
            logtxtbox.text_area("CHATBOT", logtxt, height=300)
            speak_text('Sorry at what time?')
            continue

        if (use_tag == "pickup_location" and dic["PICKUP_LOC"] == None):
            logtxt += 'Sorry didn\'t got your pickup location. Try again\n'
            logtxtbox.text_area("CHATBOT", logtxt, height=300)
            speak_text('Sorry didn\'t got your pickup location. Try again')
            continue

        if ((use_tag == "drop_time_pickup") and (dic["PICKUP_LOC"] == None or dic["DROP_LOC"] == None or dic["TIME"] == None)):
            if dic["DROP_LOC"] == None:
                logtxt += 'Sorry didn\'t got your drop location. Try again\n'
                logtxtbox.text_area("CHATBOT", logtxt, height=300)
                speak_text('Sorry didn\'t got your pickup location. Try again')

            if dic["PICKUP_LOC"] == None:
                logtxt += 'Sorry didn\'t got your pickup location. Try again\n'
                logtxtbox.text_area("CHATBOT", logtxt, height=300)
                speak_text('Sorry didn\'t got your pickup location. Try again')

            if dic["TIME"] == None:
                logtxt += 'Sorry didn\'t got that. What was the time?\n'
                logtxtbox.text_area("CHATBOT", logtxt, height=300)
                speak_text('Sorry didn\'t got your pickup location. Try again')
            continue        

        if ((use_tag == "time" or use_tag == "pickup_location" or use_tag == "drop_time_pickup") and (dic["DROP_LOC"] != None and dic["TIME"] != None and dic["PICKUP_LOC"] != None)):
            resp = 'You want to go to ' + dic["DROP_LOC"] + ' at ' + dic["TIME"] + ' from ' + dic["PICKUP_LOC"] + '. Should i confirm your ride?'
            logtxt += resp +'\n'
            logtxtbox.text_area("CHATBOT", logtxt, height=300)
            speak_text(resp)

        elif ((use_tag == "pickup_location") and (dic["TIME"] == None or dic["DROP_LOC"] == None)):
            logtxt += 'Where should i drop you to?\n'
            logtxtbox.text_area("CHATBOT", logtxt, height=300)
            speak_text('Whats the drop location?')

        if (use_tag == "confirmation" and (dic["DROP_LOC"] == None or dic["PICKUP_LOC"] == None or dic["TIME"] == None)):
            logtxt += 'Please try again.\n'
            logtxtbox.text_area("CHATBOT", logtxt, height=300)
            speak_text('Please try again.')

        else:
            logtxt += res+'\n'
            logtxtbox.text_area("CHATBOT", logtxt, height=300)
            speak_text(res)

            if use_tag == "incorrect":
                dic = {
                "DROP_LOC": None,
                "PICKUP_LOC": None,
                "TIME": None}
                continue

            if (use_tag == "confirmation" and dic["DROP_LOC"] != None and dic["PICKUP_LOC"] != None and dic["TIME"] != None) or use_tag == "phone_number" or use_tag == "account_number" or use_tag == "goodbye":
                break

    text_file(logtxt, file_name)
    one_audio()

    end_time = round(time.time() - start_time, 2)
    logtxt += '\nCall ended. Total call time: ' + str(end_time)
    logtxtbox.text_area("CHATBOT", logtxt, height=300)
    return dic, end_time

##################################  START  #####################################################
if __name__ == "__main__":
    r = sr.Recognizer()
    lemmatizer = WordNetLemmatizer()
    intents = json.loads(open('chatbot/intents.json').read())
    words = pickle.load(open('chatbot/words.pkl', 'rb'))
    classes = pickle.load(open('chatbot/classes.pkl', 'rb'))
    model = load_model('chatbot/chatbot_model.h5')
    st.set_page_config(layout="wide")

    st.write("CONVERSATIONAL AI IVR SYSTEM")

##############################  UPLOAD AUDIO OPTION  ########################################################
    raw_file = st.file_uploader("UPLOAD YOUR RECORDED MESSAGE", type = ['mp3', 'wav'])
    file_name = datetime.datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
    col1, col2, col3 = st.columns([0.9,0.9,0.12])
    placeholder1 = st.empty()
    placeholder2 = st.empty()

    with col1:
        if(st.button("Upload")):
            with placeholder1.container():
                entity, end_time = upload(raw_file, file_name)
                st.write('entities that have been extracted: ', entity)
                st.write("Total call time: ", end_time, " seconds")

#################################  CHATBOT OPTION  ######################################################
    with col2:
        if(st.button("Speak")):
            with placeholder2.container():
                final_entity, end_time = chatbot(file_name)
                st.write ('entities that have been extracted: ', final_entity)

    with col3:    
        if (st.button("Clear")):
            placeholder1.empty()
            placeholder1.empty()
