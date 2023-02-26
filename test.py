import os
import logging
import subprocess
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

# Define the output preset settings
PRESETS = {
    'Normal': ['-e', 'x264', '-q', '22'],
    'High Quality': ['-e', 'x264', '-q', '18', '--optimize'],
    'Very High Quality': ['-e', 'x265', '-q', '22', '--x265-preset', 'slow', '--x265-profile', 'main10', '--optimize'],
    'Fast 480p': ['-e', 'x264', '-q', '20', '--optimize', '--preset', 'fast', '--width', '854', '--height', '480'],
    'Fast 720p': ['-e', 'x264', '-q', '20', '--optimize', '--preset', 'fast', '--width', '1280', '--height', '720'],
}

def start(update, context):
    update.message.reply_text('Hi! Send me a video and I will transcode it using HandBrakeCLI.')

def choose_preset(update, context):
    keyboard = []
    for preset_name in PRESETS:
        keyboard.append([InlineKeyboardButton(preset_name, callback_data=preset_name)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose an output preset:', reply_markup=reply_markup)

def video_handler(update, context):
    video_file = context.bot.getFile(update.message.video.file_id, timeout=100)
    video_file_name = os.path.basename(video_file.file_path)

    if not os.path.exists('input'):
        os.makedirs('input')

    if not os.path.exists('output'):
        os.makedirs('output')

    input_file_path = os.path.join('input', video_file_name)
    video_file.download(input_file_path)

    # Check the size of the video file
    video_file_size = os.path.getsize(input_file_path)
    if video_file_size > 2 * 1024 * 1024 * 1024:  # 2 GB in bytes
        update.message.reply_text('The video file is too large and cannot be sent via Telegram.')
        return

    # Get the output preset settings from the callback data (if available) or use the 'Normal' preset as the default
    if 'preset' in context.chat_data:
        preset_name = context.chat_data['preset']
    else:
        preset_name = 'Normal'

    preset_settings = PRESETS[preset_name]

    output_file_path = os.path.join('output', f'{os.path.splitext(video_file_name)[0]}.mkv')
    subprocess.run(['HandBrakeCLI', '-i', input_file_path, '-o', output_file_path] + preset_settings)

    context.bot.send_video(chat_id=update.effective_chat.id, video=open(output_file_path, 'rb'), supports_streaming=True)

def button_handler(update, context):
    query = update.callback_query
    query.answer()

    # Set the output preset in the chat data
    context.chat_data['preset'] = query.data

    # Run the video handler to transcode the video using the new preset
    video_handler(update, context)

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

TOKEN = '6239760029:AAFBtIRSmuS-N6KtVrKourikxV7J_39nn8U'

updater = Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('preset', choose_preset))
dispatcher.add_handler(MessageHandler(filters.video, video_handler))
# Add button handler to respond to user's preset selection
dispatcher.add_handler(CallbackQueryHandler(button_handler))

# Add error handler to log any errors
dispatcher.add_error_handler(error)

# Start the bot
updater.start_polling()
updater.idle()

