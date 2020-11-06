import sys
import os
import pygame
import sqlite3
from time import time
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QGroupBox, QPushButton, QFormLayout, \
    QLabel, QListView, QInputDialog, QMessageBox, QCheckBox, QComboBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize


class MyWidget(QMainWindow):
    # инизиализация всех компонентов
    def __init__(self):
        super().__init__()
        uic.loadUi('res/design.ui', self)
        self.now_album.hide()
        self.albums.show()
        self.username = None
        self.db = sqlite3.connect("res/users.db")
        self.sql = self.db.cursor()
        # login - albums table
        self.sql.execute('''CREATE TABLE IF NOT EXISTS name (
            login TEXT,
            albums TEXT
        )''')
        # album - songs table
        self.sql.execute('''CREATE TABLE IF NOT EXISTS albums (
                    album TEXT,
                    music TEXT
        )''')
        self.db.commit()
        self.setGeometry(QApplication.desktop().width() // 4, QApplication.desktop().height() // 10, 800, 600)
        self.setWindowTitle('Mp3-player')
        self.setWindowIcon(QIcon('res/icon.jpg'))
        self.add_button.clicked.connect(self.add_folder)
        self.reload_button.setIconSize(QSize(35, 35))
        self.reload_button.clicked.connect(self.reload)
        self.back.clicked.connect(self.back_album)
        self.login_but.clicked.connect(self.login)
        self.remove_folder_but.clicked.connect(self.remove_folder)
        self.remove_album_but.clicked.connect(self.remove_albums)
        self.add_album_but.clicked.connect(self.add_album)
        self.slider.valueChanged[int].connect(self.set_song)
        self.volume.valueChanged[int].connect(self.set_volume)
        self.repeat.clicked.connect(self.repeat_change)
        self.pause_now = False
        self.play_buttons = []
        self.is_repeat = False
        self.now_song = ""
        self.remove_albums_mas = []
        # read files with tag ".mp3" in selected folders
        w = open('res/folders.txt', 'a')
        w.close()
        f = open('res/folders.txt', 'r')
        folders = f.read()
        f.close()
        self.music = []
        if (folders != ""):
            for i in folders[:-1].split("\n"):
                files = os.listdir(i)
                for j in files:
                    if j.endswith('.mp3'):
                        self.music.append(i + "/" + j)
        if self.music != []:
            self.reload()

    # ввод логина или регистрация
    def login(self):
        self.username, ok = QInputDialog.getText(self, 'Login',
                                                 'Введите имя пользователя:')
        param = "SELECT login FROM name"
        self.sql.execute(param)
        # if username is entered
        if ok:
            # register new user
            param = f"SELECT * FROM name WHERE login='{self.username}'"
            if not (bool(self.sql.execute(param).fetchall())):
                reply = QMessageBox.question(self, 'Регистрация',
                                             "Этого пользователя нет в базе, хотите\n"
                                             "зарегестрировать нового пользователя?",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == 16384:
                    self.sql.execute(f"INSERT INTO name VALUES (?, ?)",
                                     (self.username, ""))
                    self.db.commit()
                    self.username_label.setText(f"Имя пользователя: {self.username}")
                    self.reload_album()
            # login user
            else:
                self.username_label.setText(f"Имя пользователя: {self.username}")
        self.reload_album()
        self.reload()

    # add new folder with music from computer
    def add_folder(self):
        w = open('res/folders.txt', 'a')
        w.close()
        f = open('res/folders.txt', 'r')
        folders = f.read()
        f.close()
        try:
            directory = QFileDialog.getExistingDirectory(self)
            a = open('res/folders.txt', 'a')
            if (not (directory in folders)):
                a.write(directory + "\n")
            a.close()
        except:
            return
        w = open('res/folders.txt', 'a')
        w.close()
        f = open('res/folders.txt', 'r')
        folders = f.read()
        f.close()
        self.music = []
        # append folders
        if (folders != ""):
            for i in folders[:-1].split("\n"):
                files = os.listdir(i)
                for j in files:
                    if j.endswith('.mp3'):
                        self.music.append(i + "/" + j)
        self.reload()
        self.reload()

    # remove folder from path
    def remove_folder(self):
        w = open('res/folders.txt', 'a')
        w.close()
        f = open('res/folders.txt', 'r')
        folders = f.read()
        f.close()
        try:
            directory = QFileDialog.getExistingDirectory(self)
            a = open('res/folders.txt', 'w')
            if (directory in folders):
                all = folders.split("\n")
                num = all.index(directory)
                del all[num]
                end_text = ""
                for i in all:
                    if i != "":
                        end_text += i + "\n"
                a.write(end_text)
            a.close()
        except:
            return
        # reload folders.txt
        w = open('res/folders.txt', 'a')
        w.close()
        f = open('res/folders.txt', 'r')
        folders = f.read()
        f.close()
        self.music = []
        if (folders != ""):
            for i in folders[:-1].split("\n"):
                files = os.listdir(i)
                for j in files:
                    if j.endswith('.mp3'):
                        self.music.append(i + "/" + j)
        self.reload()
        self.reload()

    # add new album for user with username
    def add_album(self):
        if self.username != None:
            album_name, ok = QInputDialog.getText(self, 'Add album',
                                                  'Введите название альбома:')
            if ok:
                self.sql.execute(f"INSERT INTO name VALUES (?, ?)", (self.username, album_name))
                self.db.commit()
                self.reload_album()
        # if username == None
        else:
            QMessageBox.critical(self, "Пользователь не найден",
                                 "Сначала введите имя пользователя")
        self.reload_album()
        self.reload()

    # remove new album for user with username
    def remove_albums(self):
        for i in self.remove_albums_mas:
            self.sql.execute(f"DELETE FROM name WHERE albums = '{i}'")
        self.reload_album()
        self.db.commit()
        self.reload()

    # reload all albums (if you add or remove albums)
    def reload_album(self):
        mygroupbox = QGroupBox()
        myform = QFormLayout()
        param = f"SELECT albums FROM name WHERE login='{self.username}'"
        alb = self.sql.execute(param).fetchall()[1:]
        if alb != [('',)]:
            for i in alb:
                try:
                    self.list = QListView()
                    album_name = QLabel(i[0], self.list)
                    album_name.move(10, 10)
                    del_check = QCheckBox(self.list)
                    del_check.resize(40, 40)
                    del_check.move(600, 20)
                    del_check.stateChanged.connect(
                        lambda state=del_check.isChecked(), name=i[0]:
                        self.remove_albums_check(state, name))
                    play_button = QPushButton(self.list)
                    play_button.resize(60, 40)
                    play_button.move(660, 20)
                    play_button.setText("Go")
                    play_button.clicked.connect(lambda checked, arg=i[0]: self.switch_album(arg))
                    play_button.show()

                    myform.addRow(self.list)
                except:
                    continue
            mygroupbox.setLayout(myform)
            self.scrollArea_2.setWidget(mygroupbox)

    # all albums, which check_box is true
    def remove_albums_check(self, check, name):
        if check:
            self.remove_albums_mas.append(name)
        else:
            if (name in self.remove_albums_mas):
                del [self.remove_albums_mas[self.remove_albums_mas.index(name)]]

    # reload songs
    def reload(self):
        mygroupbox = QGroupBox()
        myform = QFormLayout()
        num = -1
        self.all_albums = []
        for i in self.music:
            num += 1
            try:
                f = open(i, "rb")
                all = f.read()
                # get song's tags
                song = all[-128 + 3:-128 + 32].decode("ptcp154").strip()
                artist = all[-128 + 33:-128 + 62].decode("ptcp154").strip()
                album = all[-128 + 63:-128 + 92].decode("ptcp154").strip()
                year = all[-128 + 93:-128 + 97].decode("ptcp154").strip()
                # create mas for all parametrs
                self.list = QListView()
                play_button = QPushButton(self.list)
                play_button.resize(40, 40)
                play_button.move(680, 20)
                play_button.clicked.connect(lambda checked, arg=i, but=play_button: self.play(arg, but))
                play_button.show()
                albums_mas = QComboBox(self.list)
                albums_mas.resize(140, 20)
                albums_mas.move(530, 40)
                param = f"SELECT albums FROM name WHERE login='{self.username}'"
                alb = self.sql.execute(param).fetchall()[1:]
                if (self.username == None):
                    albums_mas.addItem("Войдите в аккаунт")
                else:
                    albums_mas.addItem("Выберите альбом")
                    for j in alb:
                        albums_mas.addItem(j[0])
                albums_mas.currentIndexChanged[str].connect(lambda checked, arg=albums_mas,
                                                                   num=num: self.set_mas_album(arg, num))
                self.all_albums.append(None)
                add_song = QPushButton(self.list)
                add_song.resize(140, 30)
                add_song.move(530, 5)
                add_song.setText("В альбом")
                add_song.clicked.connect(lambda checked, arg=i,
                                                num=num: self.add_song_album(arg, num))
                if (i != self.now_song):
                    play_button.setIcon(QIcon('res/resume.png'))
                    play_button.setIconSize(QSize(35, 35))
                else:
                    play_button.setIcon(QIcon('res/pause.jpeg'))
                    play_button.setIconSize(QSize(35, 35))
                self.play_buttons.append(play_button)
                self.label = QLabel("Название: " + song, self.list)
                self.label.move(5, 10)
                self.label = QLabel("Исполнитель: " + artist, self.list)
                self.label.move(5, 40)
                self.label = QLabel("Год выпуска: " + year, self.list)
                self.label.move(300, 10)
                self.label = QLabel("Альбом: " + album, self.list)
                self.label.move(300, 40)
                myform.addRow(self.list)
            except:
                continue
        mygroupbox.setLayout(myform)
        self.scrollArea.setWidget(mygroupbox)

    # stop all proceses, then app is closed
    def closeEvent(self, event):
        self.done = 2

    # play, pause a songs
    def play(self, name, button):
        self.done = 2
        f = open(name, "rb")
        all = f.read()
        song = all[-128 + 3:-128 + 32].decode("ptcp154").strip()
        artist = all[-128 + 33:-128 + 62].decode("ptcp154").strip()
        self.now_playing.setText(f"{artist} - {song}")
        try:
            self.last_button.setIcon(QIcon('res/resume.png'))
        except:
            1
        self.last_button = button
        SONG_FINISHED = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(SONG_FINISHED)
        if (self.now_song != name or self.is_repeat):
            self.now_time = 0
            self.slider.setValue(0)
            button.setIcon(QIcon('res/pause.jpeg'))
            button.setIconSize(QSize(35, 35))
            self.pause_now = False
            pygame.init()
            pygame.mixer.music.load(name)
            pygame.mixer.music.play()
            self.now_song = name
        else:
            if (not (self.pause_now)):
                pygame.mixer.music.pause()
                self.pause_now = not (self.pause_now)
                button.setIcon(QIcon('res/resume.png'))
                button.setIconSize(QSize(35, 35))
            else:
                button.setIcon(QIcon('res/pause.jpeg'))
                button.setIconSize(QSize(35, 35))
                pygame.mixer.music.unpause()
                self.pause_now = not (self.pause_now)
        self.done = 0
        self.sound_len = int(pygame.mixer.Sound(name).get_length())
        if self.sound_len == 0:
            self.sound_len = 1
        last_perc = 0
        time_1 = time()
        time_2 = time()
        while self.done < 1:
            for event in pygame.event.get():
                if event.type == SONG_FINISHED:
                    self.done = 1
                    break
                elif event.type == pygame.QUIT:
                    self.done = 1
                    break
            if (not (self.pause_now)):
                self.now_time += time_1 - time_2
            perc = int(self.now_time / self.sound_len * 100)
            if perc != last_perc:
                self.changed = False
                self.slider.setValue(perc)
                last_perc = perc
            time_2 = time_1
            time_1 = time()
        button.setIcon(QIcon('res/resume.png'))
        button.setIconSize(QSize(35, 35))
        if (self.done == 2):
            pygame.quit()
            return 1
        if (self.music.index(name) + 1 < len(self.music)):
            next_m = self.music.index(name) + 1
        else:
            next_m = 0
        if (self.play_buttons.index(button) + 1 < len(self.play_buttons)):
            next_b = self.play_buttons.index(button) + 1
        else:
            next_b = 0
        if self.is_repeat:
            next_b = self.play_buttons.index(button)
            next_m = self.music.index(name)
            pygame.mixer.music.stop()
        self.play(self.music[next_m],
                  self.play_buttons[next_b])

    # set moment in the song with slider
    def set_song(self, value):
        try:
            if (self.changed):
                pygame.mixer.music.set_pos(value / 100 * self.sound_len)
                self.now_time = value / 100 * self.sound_len
            else:
                self.changed = True
        except:
            pass

    def set_volume(self, value):
        volume = value / 100
        if(volume <= 1):
            pygame.mixer.music.set_volume(volume)

    def set_mas_album(self, item, num):
        self.all_albums[num] = item.currentText()

    def add_song_album(self, name, num):
        if not (bool(self.sql.execute(f"SELECT * FROM albums WHERE music='{name}'").fetchall())):
            self.sql.execute(f"INSERT INTO albums VALUES (?, ?)", (self.all_albums[num], name))
            self.db.commit()

    def back_album(self):
        self.albums.show()
        self.now_album.hide()

    def switch_album(self, name):
        self.now_album.show()
        self.albums.hide()
        param = f"SELECT music FROM albums WHERE album='{name}'"
        songs = self.sql.execute(param).fetchall()
        mygroupbox = QGroupBox()
        myform = QFormLayout()
        self.play_buttons_album = []
        self.music_album = []
        for i in songs:
            try:
                self.music_album.append(i[0])
                f = open(i[0], "rb")
                all = f.read()
                song = all[-128 + 3:-128 + 32].decode("ptcp154").strip()
                artist = all[-128 + 33:-128 + 62].decode("ptcp154").strip()
                album = all[-128 + 63:-128 + 92].decode("ptcp154").strip()
                year = all[-128 + 93:-128 + 97].decode("ptcp154").strip()
                # create mas for all parametrs
                self.list = QListView()
                play_button = QPushButton(self.list)
                play_button.resize(40, 40)
                play_button.move(680, 20)
                play_button.clicked.connect(lambda checked, arg=i[0], but=play_button: self.play_album(arg, but))
                play_button.show()
                if (i != self.now_song):
                    play_button.setIcon(QIcon('res/resume.png'))
                    play_button.setIconSize(QSize(35, 35))
                else:
                    play_button.setIcon(QIcon('res/pause.jpeg'))
                    play_button.setIconSize(QSize(35, 35))
                self.play_buttons_album.append(play_button)
                self.label = QLabel("Название: " + song, self.list)
                self.label.move(5, 10)
                self.label = QLabel("Исполнитель: " + artist, self.list)
                self.label.move(5, 40)
                self.label = QLabel("Год выпуска: " + year, self.list)
                self.label.move(300, 10)
                self.label = QLabel("Альбом: " + album, self.list)
                self.label.move(300, 40)
                myform.addRow(self.list)
            except:
                continue
        mygroupbox.setLayout(myform)
        self.album_music_area.setWidget(mygroupbox)

    def play_album(self, name, button):
        self.done = 2
        f = open(name, "rb")
        all = f.read()
        if all != "":
            song = all[-128 + 3:-128 + 32].decode("ptcp154").strip()
            artist = all[-128 + 33:-128 + 62].decode("ptcp154").strip()
            self.now_playing.setText(f"{artist} - {song}")
        try:
            self.last_button.setIcon(QIcon('res/resume.png'))
        except:
            1
        self.last_button = button
        SONG_FINISHED = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(SONG_FINISHED)
        if (self.now_song != name):
            self.now_time = 0
            self.slider.setValue(0)
            button.setIcon(QIcon('res/pause.jpeg'))
            button.setIconSize(QSize(35, 35))
            self.pause_now = False
            pygame.init()
            pygame.mixer.music.load(name)
            pygame.mixer.music.play()
            self.now_song = name
        else:
            if (not (self.pause_now)):
                pygame.mixer.music.pause()
                self.pause_now = not (self.pause_now)
                button.setIcon(QIcon('res/resume.png'))
                button.setIconSize(QSize(35, 35))
            else:
                button.setIcon(QIcon('res/pause.jpeg'))
                button.setIconSize(QSize(35, 35))
                pygame.mixer.music.unpause()
                self.pause_now = not (self.pause_now)
        self.done = 0
        self.sound_len = int(pygame.mixer.Sound(name).get_length())
        last_perc = 0
        time_1 = time()
        time_2 = time()
        while self.done < 1:
            for event in pygame.event.get():
                if event.type == SONG_FINISHED:
                    self.done = 1
                    break
                if event.type == pygame.QUIT:
                    self.done = 1
                    break
            if (not (self.pause_now)):
                self.now_time += time_1 - time_2
            perc = int(self.now_time / self.sound_len * 100)
            if perc != last_perc:
                self.changed = False
                self.slider.setValue(perc)
                last_perc = perc
            time_2 = time_1
            time_1 = time()
        if (self.done == 2):
            return 1
        button.setIcon(QIcon('res/resume.png'))
        button.setIconSize(QSize(35, 35))
        if (self.music_album.index(name) + 1 < len(self.music_album)):
            next_m = self.music_album.index(name) + 1
        else:
            next_m = 0
        if (self.play_buttons_album.index(button) + 1 < len(self.play_buttons_album)):
            next_b = self.play_buttons_album.index(button) + 1
        else:
            next_b = 0

        if self.is_repeat:
            next_m = self.music_album.index(name)
            next_b = self.play_buttons_album.index(button)


        self.play(self.music_album[next_m],
                  self.play_buttons_album[next_b])

    def repeat_change(self):
        self.is_repeat = not(self.is_repeat)
        if(self.is_repeat):
            self.repeat.setStyleSheet('background-color: #8A7F8E')
        else:
            self.repeat.setStyleSheet('background-color: #FFFFFF')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())