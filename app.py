from IPython.display import Javascript
from IPython import display
from base64 import b64decode
import datetime
import whisper
import openai
import os
import base64
from Crypto.Cipher import AES

import streamlit as st

from tempfile import NamedTemporaryFile



RECORD = """
const sleep  = time => new Promise(resolve => setTimeout(resolve, time))
const b2text = blob => new Promise(resolve => {
  const reader = new FileReader()
  reader.onloadend = e => resolve(e.srcElement.result)
  reader.readAsDataURL(blob)
})
var record = time => new Promise(async resolve => {
  stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  recorder = new MediaRecorder(stream)
  chunks = []
  recorder.ondataavailable = e => chunks.push(e.data)
  recorder.start()
  await sleep(time)
  recorder.onstop = async ()=>{
    blob = new Blob(chunks)
    text = await b2text(blob)
    resolve(text)
  }
  recorder.stop()
})
"""

openai.api_key = st.secrets["API_KEY"]

with open("encrypt.txt", "r") as encfile:
  encoder_txt = encfile.read()

with open("decrypt.txt", "r") as decfile:
  decoder_txt = decfile.read()

def openai_fun(myprompt):
  response_encoded = openai.Completion.create(
                engine="text-davinci-003",
                prompt = myprompt,
                max_tokens=1024,
                n=1,
                stop=None,
                temperature=0.5,
            )
  return response_encoded

def record(sec=5):
    stt_button = Button(label="Record", width=100)
    stt_button.js_on_event("button_click", CustomJS(code="""
        var mediaRecorder;
        if (!mediaRecorder) {
            navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
                mediaRecorder = new MediaRecorder(stream);
                var chunks = [];
                mediaRecorder.ondataavailable = function(e) {
                    chunks.push(e.data);
                };
                mediaRecorder.start();
                setTimeout(function() {
                    mediaRecorder.stop();
                    var blob = new Blob(chunks, { 'type' : 'audio/webm; codecs=opus' });
                    var reader = new FileReader();
                    reader.onload = function(e) {
                        var base64 = btoa(e.target.result);
                        document.dispatchEvent(new CustomEvent("GET_AUDIO", {detail: base64}));
                    };
                    reader.readAsBinaryString(blob);
                    stream.getTracks().forEach(function(track) {
                        track.stop();
                    });
                }, 5000);
            }).catch(function(err) {
                console.log('Error: ' + err);
            });
        }
        """))
    result = streamlit_bokeh_events(
        stt_button,
        events="GET_AUDIO",
        key="listen",
        refresh_on_update=False,
        override_height=75,
        debounce_time=0)
    
    if result:
        
        audio_data = result['GET_AUDIO']
        
        audio_bytes = base64.b64decode(audio_data)
        return audio_bytes


    else:
       st.write("RESULT")  
       return None
  

model = whisper.load_model("base")
transcribed = []


user_choice = st.file_uploader(label="Upload audio file",type=['.wav'])

if user_choice is not None:
  with NamedTemporaryFile(suffix="wav") as temp:
    temp.write(user_choice.getvalue())
    temp.seek(0)
    model = whisper.load_model("base")
    result = model.transcribe(temp.name)
    st.write(f'Original message: {result["text"]}')
    
  
  

  #audio = whisper.load_audio(user_choice)
  #audio = whisper.pad_or_trim(audio)
  #mel = whisper.log_mel_spectrogram(audio).to(model.device)
  #options = whisper.DecodingOptions(language= 'en', fp16=False)

  #result = whisper.decode(model, mel, options)

  
  mymsg = result["text"]
  st.write("Actual Message: ",mymsg)

  enc_prompt = encoder_txt + mymsg

  openai_fun(enc_prompt)

  if openai_fun(enc_prompt)['choices'][0]['text'] != "":
      # print(response_encoded['choices'][0]['text'])
      exec(openai_fun(enc_prompt)['choices'][0]['text'])
      encoded_msg = enc(mymsg)
      st.write("The encoded message: ", encoded_msg)

      decode_ = st.text_input("Do you wish to decode the message?[y/n]").strip()
      if decode_ == "y":
            dec_prompt = decoder_txt + str(encoded_msg)
            response_decoded = openai.Completion.create(
              engine="text-davinci-003",
              prompt = dec_prompt,
              max_tokens=500,
              n=1,
              stop=None,
              temperature=0.5,
            )

            if response_decoded['choices'][0]['text'] != "":
                print(response_decoded['choices'][0]['text'])
                exec(response_decoded['choices'][0]['text'])
                decoded_msg = dec(encoded_msg, key)
                st.write("The decoded message: ", decoded_msg)
      else: st.write('Thanks for using the app!')



  else:
      st.write('Retry! The message could')


  #break # exit the loop

else:
    pass
    # uc1 = input('Do you want to transcribe an existing audio?[y/n]')
    
    # if uc1 == 'y':
    #   folder_path = "/content"
    #   audio_files = [f for f in os.listdir(folder_path) if f.endswith(".wav")]
    #   print('Audio files present: ',audio_files)

    #   audio_files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)
    #   last_audio_file_path = os.path.join(folder_path, audio_files[0])
    #   print('Transcribing last audio file: ',last_audio_file_path)

    #   # COMMENT IF NOT NEEDED:
    #   if os.path.exists(last_audio_file_path) and not last_audio_file_path in transcribed:
    #     audio = whisper.load_audio(last_audio_file_path)
    #     audio = whisper.pad_or_trim(audio)
    #     mel = whisper.log_mel_spectrogram(audio).to(model.device)
    #     options = whisper.DecodingOptions(language= 'en', fp16=False)

    #     result = whisper.decode(model, mel, options)

    #     if result.no_speech_prob < 0.5:
    #         mymsg = result.text
    #         print("Actual Message: ",mymsg)
    #         enc_prompt = encoder_txt + result.text
    #         response_encoded = openai.Completion.create(
    #             engine="text-davinci-003",
    #             prompt = enc_prompt,
    #             max_tokens=1024,
    #             n=1,
    #             stop=None,
    #             temperature=0.5,
    #         )
            
    #         if response_encoded['choices'][0]['text'] != "":
    #           # print(response_encoded['choices'][0]['text'])
    #           exec(response_encoded['choices'][0]['text'])
    #           encoded_msg = enc(mymsg)
    #           st.write("The encoded message: ", encoded_msg)

    #         else:
    #             st.write('Retry! The message could')
            
    #         # DELETE audio

    #   break # exit the loop

    # elif uc1 == 'n':
    #   continue # continue the loop, prompting for input again

    # else:
    #   st.write('Invalid input, please enter y or n')
    #   continue # continue the loop, prompting for input again

