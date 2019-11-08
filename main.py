from threading import Thread

from video_handler import VideoHandler
from doorbell_bot import bot

if __name__ == "__main__":
    video_handler = VideoHandler(bot)
    Thread(target=bot.polling).start()
    Thread(target=video_handler.video_capture_loop).start()
