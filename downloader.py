import sys
import os
from bs4 import BeautifulSoup

from urllib2 import urlopen, URLError
from urllib import quote_plus as qp

from PySide.QtGui import QApplication, QMainWindow, QIcon, QFileDialog, QMessageBox
from PySide.QtCore import QProcess

from ui_downloader import Ui_MainWindow

__version__ = '0.0.2'


class YouTube:
    def __init__(self):
        self.homedir = os.path.join(os.path.expanduser("~"), '.ytd')
        if not os.path.exists(self.homedir):
            os.makedirs(self.homedir)
        self.version_file = os.path.join(self.homedir, 'youtube-dl.version')

    def download_file(self, url, ytd=None):
        u = urlopen(url)
        meta = u.info()
        file_size = int(meta.getheaders('Content-Length')[0])
        print file_size

        f = open(os.path.join(self.homedir, os.path.basename(url)), 'wb')

        downloaded_bytes = 0
        block_size = 1024 * 512
        while True:
            buffer = u.read(block_size)
            if not buffer:
                break

            f.write(buffer)
            downloaded_bytes += block_size
            print downloaded_bytes

        if ytd:
            open(self.version_file, 'w').write(url)

    def check_ffmpeg(self):
        if not os.path.exists(os.path.join(self.homedir, 'ffmpeg.exe')):
            return 'http://ffmpeg.jagnet.biz/ffmpeg.exe'
        else:
            return None

    def check_ffprobe(self):
        if not os.path.exists(os.path.join(self.homedir, 'ffprobe.exe')):
            return 'http://ffmpeg.jagnet.biz/ffprobe.exe'
        else:
            return None

    def get_exe_url(self):
        try:
            html = urlopen('https://rg3.github.io/youtube-dl/download.html').read()
            soup = BeautifulSoup(html, 'html.parser')
            for link in soup.find_all('a'):
                if link.get('href').endswith('exe'):
                    return link.get('href')
        except:
            return None

    def check_version(self):
        if not os.path.exists(self.version_file):
            open(self.version_file, 'w').close()
        curr_version = open(self.version_file, 'r').read()
        remote_version = self.get_exe_url()
        if curr_version != remote_version and remote_version is not None:
            return remote_version
        elif remote_version is None:
            return 'Unable to get version'
        else:
            return None

    def search(self, search_term):
        if search_term and search_term != '':
            search_term = qp(search_term)
            try:
                response = urlopen('https://www.youtube.com/results?search_query=' + search_term)

                html = response.read()
                soup = BeautifulSoup(html, 'html.parser')
                for link in soup.find_all('a'):
                    if '/watch?v=' in link.get('href'):
                        video_link = link.get('href')
                        break

                title = soup.find("a", "yt-uix-tile-link").text
            except URLError, e:
                title = 'Unable to search ({0})'.format(e.reason)
                video_link = ''
            return {'title': title, 'video_link': video_link}

    def video_download(self, video_link, outputdir):
        command = '''{2}\\youtube-dl --output "{0}/%(title)s.%(ext)s" "{1}"'''.format(outputdir, video_link, self.homedir)
        print command
        os.system(command)

    def audio_download(self, video_link, outputdir):
        command = '''{2}\\youtube-dl --extract-audio \
--audio-format mp3 --audio-quality 0 --output "{0}/%(title)s.%(ext)s" "{1}"'''.format(outputdir,
                                                                                      video_link,
                                                                                      self.homedir)
        os.system(command)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setup_form()

        self.rbUrl.clicked.connect(self.source_rb_changed)
        self.rbSearch.clicked.connect(self.source_rb_changed)

        self.txtbxSearch.returnPressed.connect(self.youtube_search)
        self.btnSearch.clicked.connect(self.youtube_search)

        self.btnOutputDir.clicked.connect(self.output_folder_chooser)

        self.btnDownload.clicked.connect(self.download_youtube_media)

        self.process = QProcess(self)
        # QProcess emits `readyRead` when there is data to be read
        self.process.readyRead.connect(self.dataReady)

        self.process.started.connect(lambda: self.btnDownload.setEnabled(False))
        self.process.finished.connect(lambda: self.btnDownload.setEnabled(True))

        self.yt = YouTube()
        self.youtube_dl_version_check()
        self.ffmpeg_check()
        self.ffprobe_check()

    def setup_form(self):
        self.btnSearch.setEnabled(False)
        self.txtbxUrl.setEnabled(False)
        self.txtbxSearch.setEnabled(False)
        self.rbDlVideo.toggle()
        self.btnDownload.setEnabled(False)
        self.check_dl_ready()

    def check_dl_ready(self):
        if self.lblOutputDir.text() != '' and self.txtbxUrl.text() != '':
            self.btnDownload.setEnabled(True)
        else:
            self.btnDownload.setEnabled(False)

    def youtube_dl_version_check(self):
        new_version = self.yt.check_version()
        if new_version and new_version != 'Unable to get version':
            res = QMessageBox.warning(self,
                                      "youtube-dl version check",
                                      """A new version of youtube-dl is available, would you like to download it now?""",
                                      QMessageBox.Yes | QMessageBox.No,
                                      WindowModility=True)
            if res == QMessageBox.StandardButton.Yes:
                self.yt.download_file(new_version, True)
        elif new_version == 'Unable to get version':
            QMessageBox.warning(self,
                                "youtube-dl version check",
                                """Unable to determine the current version of youtube-dl""",
                                QMessageBox.Ok,
                                WindowModility=True)

    def ffmpeg_check(self):
        ffmpeg_url = self.yt.check_ffmpeg()
        if ffmpeg_url:
            res = QMessageBox.warning(self,
                                      "ffmpeg check",
                                      """ffmpeg is missing, without this you will not be able to download mp3 files.
Would you like to download it now?""",
                                      QMessageBox.Yes | QMessageBox.No,
                                      WindowModility=True)
            if res == QMessageBox.StandardButton.Yes:
                self.yt.download_file(ffmpeg_url)

    def ffprobe_check(self):
        ffprobe_url = self.yt.check_ffprobe()
        if ffprobe_url:
            res = QMessageBox.warning(self,
                                      "ffprobe check",
                                      """ffprobe is missing, without this you will not be able to download mp3 files.
Would you like to download it now?""",
                                      QMessageBox.Yes | QMessageBox.No,
                                      WindowModility=True)
            if res == QMessageBox.StandardButton.Yes:
                self.yt.download_file(ffprobe_url)

    def source_rb_changed(self):
        if self.rbUrl.isChecked():
            self.btnSearch.setEnabled(False)
            self.txtbxSearch.setEnabled(False)
            self.txtbxUrl.setEnabled(True)
        elif self.rbSearch.isChecked():
            self.btnSearch.setEnabled(True)
            self.txtbxSearch.setEnabled(True)
            self.txtbxUrl.setEnabled(False)
        else:
            self.txtbxSearch.setEnabled(False)
            self.txtbxUrl.setEnabled(False)
        self.check_dl_ready()

    def youtube_search(self):
        self.statusbar.showMessage('Searching Youtube...')
        search_term = self.txtbxSearch.text()
        search_res = self.yt.search(search_term)
        if search_res.get('title') != 'Not Found':
            QMessageBox.information(self,
                                    "YouTube Search Results",
                                    """Your search term returned the following video:\n{0}""".format(search_res.get('title')),
                                    QMessageBox.Ok)
            self.txtbxUrl.setText('http://www.youtube.com{0}'.format(search_res.get('video_link')))
        else:
            QMessageBox.critical(self,
                                 "YouTube Search Results",
                                 """Your search term returned no results""",
                                 QMessageBox.Ok)
        self.statusbar.clearMessage()
        self.check_dl_ready()

    def output_folder_chooser(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly)
        dialog.exec_()
        dirname = os.path.abspath(dialog.directory().absolutePath())
        self.lblOutputDir.setText(dirname)
        self.check_dl_ready()

    def dataReady(self):
        cursor = self.txtOutputText.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(str(self.process.readAll()))
        self.txtOutputText.ensureCursorVisible()

    def download_youtube_media(self):
        self.btnDownload.setEnabled(False)
        if self.txtbxUrl.text() == '':
            QMessageBox.critical(self,
                                 "No video file selected",
                                 """Please select a file that you wish to download""",
                                 WindowModility=True)
            self.btnDownload.setEnabled(True)
            return
        if self.lblOutputDir.text() == '':
            QMessageBox.critical(self,
                                 "No output direcotry selected",
                                 """Please select an output directory""",
                                 WindowModility=True)
            self.btnDownload.setEnabled(True)
            return

        self.statusbar.showMessage('Downloading file...')
        self.start_download()

    def start_download(self):
        outputdir = str(self.lblOutputDir.text()).replace('\\', '/')
        if self.rbDlVideo.isChecked():
            itemtype = 'video'
            self.yt.video_download(self.txtbxUrl.text(), outputdir,)
            # '''youtube-dl --proxy "" --output "{0}/%(title)s" "{1}"'''.format(outputdir, video_link)
            # params = ['--proxy \"\"', '--output \"{0}/%(title)s\"'.format(outputdir), '\"{0}\"'.format(self.txtbxUrl.text())]
        elif self.rbDlAudio.isChecked():
            itemtype = 'audio'
            self.yt.audio_download(self.txtbxUrl.text(), outputdir,)
        # self.process.execute(os.path.join(os.getcwd(), 'youtube-dl.exe'), params)
        self.statusbar.clearMessage()
        QMessageBox.information(self,
                                "YouTube Download Complete",
                                """Your {0} has been successfully downloaded""".format(itemtype),
                                QMessageBox.Ok)
        self.btnDownload.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    if getattr(sys, 'frozen', False):
        # frozen
        appdir = os.path.dirname(sys.executable)
    else:
        # unfrozen
        appdir = os.path.dirname(os.path.realpath(__file__))
    app.setWindowIcon(QIcon(os.path.join(appdir, 'ytd.ico')))
    frame = MainWindow()
    frame.show()
    app.exec_()


if __name__ == '__main__':
    main()
