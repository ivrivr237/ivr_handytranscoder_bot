import logging
import subprocess
import telebot
import time
import re
import os
from telebot.types import Message

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot('6239760029:AAFBtIRSmuS-N6KtVrKourikxV7J_39nn8U')

@bot.message_handler(commands=['start'])
def handle_start(message: Message) -> None:
    bot.reply_to(message, 'Hi! Send me a video file and I will transcode it using HandBrake CLI.')

@bot.message_handler(content_types=['video'])
def handle_video(message: Message) -> None:
    # Create input and output folders if they don't exist
    if not os.path.exists('input'):
        os.mkdir('input')
    if not os.path.exists('output'):
        os.mkdir('output')
    
    # Download the video file
    file_info = bot.get_file(message.video.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    # Transcode the video using HandBrake CLI
    with open('input/input.mp4', 'wb') as f:
        f.write(downloaded_file)
    command = ['HandBrakeCLI', '-i', 'input/input.mp4', '-o', 'output/output.mp4']
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    
    # Send status messages to the user every 3 seconds while transcoding
    while p.poll() is None:
        output = p.stdout.readline()
        if not output:
            break
        # Extract progress information from HandBrake CLI output
        percent_match = re.search(r'\b(\d+(?:\.\d+)?)%\b', output)
        fps_match = re.search(r'\b(\d+(?:\.\d+)?) fps\b', output)
        eta_match = re.search(r'\bETA (\d+):(\d+):(\d+)\b', output)
        if percent_match and fps_match and eta_match:
            percent = percent_match.group(1)
            fps = fps_match.group(1)
            eta_hours = int(eta_match.group(1))
            eta_minutes = int(eta_match.group(2))
            eta_seconds = int(eta_match.group(3))
            eta = f'{eta_hours:02d}:{eta_minutes:02d}:{eta_seconds:02d}'
            message_text = f'Transcoding video... {percent}% complete, {fps} fps, ETA {eta}'
            bot.send_message(message.chat.id, message_text)
        time.sleep(3)
    
    # Delete the input video file
    os.remove('input/input.mp4')
    
    # Check if transcoding process had an error
    if p.returncode != 0:
        error_message = 'An error occurred while transcoding the video. Please try again.'
        bot.send_message(message.chat.id, error_message)
    else:
        # Send the transcoded video back to the user
        with open('output/output.mp4', 'rb') as f:
            bot.send_video(message.chat.id, f)
        
        # Delete the output video file
        os.remove('output/output.mp4')
        
bot.polling()

