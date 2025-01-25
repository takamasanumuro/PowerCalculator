import chime
import time
def play_success_sound():
    previous_theme = chime.theme()
    chime.theme('big-sur')
    chime.success()
    time.sleep(2)
    chime.theme(previous_theme)

if __name__ == "__main__":
    play_success_sound()