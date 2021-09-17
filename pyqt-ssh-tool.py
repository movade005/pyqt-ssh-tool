from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QAction, QDialog, QMessageBox, QTreeWidgetItem
from ui import main, add_config, text_editor, confirm
import sys
import os
from function import ssh_func, get_running_data
import threading
import paramiko
from PyQt5.QtCore import QTimer, QUrl, pyqtSignal, QEvent, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QIcon, QTextCursor, QCursor, QCloseEvent, QKeyEvent, QInputMethodEvent
import time
import pickle


# 主界面逻辑
class MainDialog(QMainWindow):
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__(parent)
        self.ui = main.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))
        self.setAttribute(Qt.WA_InputMethodEnabled, True)
        self.setAttribute(Qt.WA_KeyCompression, True)
        self.setFocusPolicy(Qt.WheelFocus)

        self.ui.Shell.setAttribute(Qt.WA_InputMethodEnabled, True)
        self.ui.Shell.setAttribute(Qt.WA_KeyCompression, True)

        self.ssh_conn = None
        self.sign = b''
        self.timer, self.timer1 = None, None
        self.getsysinfo = None
        self.dir_tree_now = []
        self.pwd = ''
        self.file_name = ''

        self.ssh_username, self.ssh_password, self.ssh_ip = None, None, None

        self.ui.discButton.clicked.connect(self.disconnect)
        self.ui.seeOnline.clicked.connect(self.get_run_data)
        self.ui.setWan.clicked.connect(self.get_run_data)
        self.ui.setLan.clicked.connect(self.get_run_data)
        self.ui.init.clicked.connect(self.get_run_data)
        self.ui.showPort.clicked.connect(self.get_run_data)
        self.ui.webview.clicked.connect(self.open_web)
        self.ui.timezoneButton.clicked.connect(self.get_run_data)
        self.ui.treeWidget.customContextMenuRequested.connect(self.tree_right)
        self.ui.treeWidget.doubleClicked.connect(self.cd)

        self.isConnected = False

    # 连接服务器
    def connect(self):
        focus = self.ui.treeWidget.currentIndex().row()
        if focus != -1:
            name = self.ui.treeWidget.topLevelItem(focus).text(0)
            with open('config.dat', 'rb') as c:
                conf = pickle.loads(c.read())[name]
                c.close()
            username, password, host = conf[0], conf[1], conf[2]
            try:
                self.ssh_conn = ssh_func.SshClient(host.split(':')[0], int(host.split(':')[1]), username, password)
                self.ssh_conn.connect()
            except Exception as e:
                self.ui.Shell.setPlaceholderText(str(e))
            self.ssh_username, self.ssh_password, self.ssh_ip = username, password, host
            if self.ssh_conn.session is not None:
                self.isConnected = True
                self.ui.discButton.setEnabled(True)
                self.ui.seeOnline.setEnabled(True)
                self.ui.result.setEnabled(True)
                self.ui.lanIP.setEnabled(True)
                self.ui.wanIP.setEnabled(True)
                self.ui.gateway.setEnabled(True)
                self.ui.setWan.setEnabled(True)
                self.ui.setLan.setEnabled(True)
                self.ui.initKey.setEnabled(True)
                self.ui.init.setEnabled(True)
                self.ui.webview.setEnabled(True)
                self.ui.showPort.setEnabled(True)
                self.ui.webview.setEnabled(True)
                self.ui.iport.setEnabled(True)
                self.ui.Shell.setEnabled(True)
                self.ui.timezoneButton.setEnabled(True)
                th1 = threading.Thread(target=self.ssh_conn.receive, daemon=True)
                th1.start()
                self.getsysinfo = get_running_data.DevicInfo(username=conf[0], password=conf[1], host=conf[2])
                th3 = threading.Thread(target=self.getsysinfo.get_datas, daemon=True)
                th3.start()
                self.flush()
                self.flush_sysinfo()
                self.refresh_dirs()
            else:
                pass
        else:
            self.alarm('请选择一台设备！')

    # 后台获取信息，不打印至程序界面
    def get_data2(self, cmd='', pty=False):
        try:
            ack = self.ssh_conn.exec(cmd=cmd, pty=pty)
            # print(ack)
            return ack
        except Exception as e:
            self.ui.result.append(e)
            return 'error'

    # 选择文件夹
    def cd(self):
        if self.isConnected:
            focus = self.ui.treeWidget.currentIndex().row()
            if focus != -1 and self.dir_tree_now[focus][0].startswith('d'):
                self.pwd = self.get_data2('cd '+self.pwd+'/'+self.ui.treeWidget.topLevelItem(focus).text(0) +
                                          ' && sudo pwd')[:-1]
                self.refresh_dirs()
            else:
                self.alarm('文件无法前往，右键编辑文件！')
        elif not self.isConnected:
            self.connect()

    # 断开服务器
    def disconnect(self):
        self.ssh_conn.term_data = b''
        self.ssh_conn.diconnect()
        self.isConnected = False
        self.ssh_username, self.ssh_password, self.ssh_ip = None, None, None
        self.ui.discButton.setDisabled(True)
        self.ui.seeOnline.setDisabled(True)
        self.ui.result.setDisabled(True)
        self.ui.Shell.setDisabled(True)
        self.ui.iport.setDisabled(True)
        self.ui.lanIP.setDisabled(True)
        self.ui.wanIP.setDisabled(True)
        self.ui.webview.setDisabled(True)
        self.ui.gateway.setDisabled(True)
        self.ui.setWan.setDisabled(True)
        self.ui.setLan.setDisabled(True)
        self.ui.initKey.setDisabled(True)
        self.ui.init.setDisabled(True)
        self.ui.webview.setDisabled(True)
        self.ui.showPort.setDisabled(True)
        self.ui.timezoneButton.setDisabled(True)
        self.getsysinfo.disconnect()
        self.refresh_conf()

    # 定时刷新shell
    def flush(self):
        self.timer = QTimer()
        self.timer.start(15)
        self.timer.timeout.connect(self.refresh_xterm)

    # 刷新shell
    def refresh_xterm(self):
        if self.isConnected is True:
            if self.isConnected is True and self.sign != self.ssh_conn.buffer3:
                to_show = self.ssh_conn.buffer3
                self.ui.Shell.setPlainText(to_show)
                self.ui.Shell.moveCursor(QTextCursor.End)
                self.sign = self.ssh_conn.buffer3
            elif self.sign == self.ssh_conn.buffer3:
                pass

    # 键盘事件， shell输入
    def keyReleaseEvent(self, a0: QKeyEvent) -> None:
        print(a0.text())
        try:
            if a0.key() == 16777219:
                self.ssh_conn.send(b'\x08')
            elif a0.key() == 16777219:
                self.ssh_con.send(b'\x09')
            elif a0.key() == 16777235:
                self.ssh_conn.send(b'\x1b[A')
            elif a0.key() == 16777237:
                self.ssh_conn.send(b'\x1b[B')
            elif a0.key() == 16777234:
                self.ssh_conn.send(b'\x1b[D')
            elif a0.key() == 16777236:
                self.ssh_conn.send(b'\x1b[C')
            elif a0.key() == 16777220:
                self.ssh_conn.buffer1 = ['|', '']
                self.ssh_conn.send(b'\r')
            else:
                self.ssh_conn.send(a0.text().encode('utf8'))
        except Exception as e:
            self.ui.result.append(e)

    def inputMethodEvent(self, a0: QInputMethodEvent) -> None:
        cmd = a0.commitString()
        print(cmd)
        if cmd != '':
            self.ssh_conn.send(cmd.encode('utf8'))

    # 服务器运行命令并获取输出
    def get_run_data(self, cmd=''):
        sender = self.sender()
        cmd = cmd
        if sender.objectName() == 'seeOnline':
            cmd = 'sudo nmap -sP '+self.ui.iport.text()
        elif sender.objectName() == 'init':
            cmd = self.ui.initKey.toPlainText()
        elif sender.objectName() == 'setWan':
            ip, gateway = self.ui.wanIP.text(), self.ui.gateway.text()
            cmd = 'sudo nmcli connection modify eth0 ipv4.addresses '+ip+' ipv4.gateway ' + gateway + \
                  ' && nmcli connection show eth0'
        elif sender.objectName() == 'setLan':
            ip = self.ui.lanIP.text()
            cmd = 'sudo nmcli connection modify eth0 +ipv4.addresses ' + ip + \
                  ' && nmcli connection show eth0'
        elif sender.objectName() == 'showPort':
            ip = self.ui.iport.text()
            cmd = 'sudo nmap -PN '+ip
        elif sender.objectName() == 'timezoneButton':
            cmd = 'sudo timedatectl set-timezone "Asia/Shanghai" && sudo hwclock'
        else:
            pass
        self.ui.progressBar.setValue(20)
        username, password, host = self.ssh_username, self.ssh_password, self.ssh_ip
        self.ui.result.append(cmd)
        if self.isConnected is True:
            try:
                # 创建SSH对象
                ssh = paramiko.SSHClient()
                # 允许连接不在know_hosts文件中的主机
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                # 连接服务器
                ssh.connect(hostname=host.split(':')[0], port=int(host.split(':')[1]),
                            username=username, password=password, timeout=3)
                self.ui.progressBar.setValue(50)
                # 执行命令
                stdin, stdout, stderr = ssh.exec_command(timeout=10, bufsize=100, command=cmd)
                # 获取命令结果
                ack = stdout.read().decode('utf8')
                self.ui.result.append(ack)
                self.ui.progressBar.setValue(80)
                time.sleep(0.1)
                # ssh.close()
                self.ui.progressBar.setValue(100)
                return ack
            except Exception as e:
                self.ui.result.append(str(e))
                self.ui.progressBar.setValue(100)
        else:
            self.ui.result.append('请先连接设备!')
            self.ui.progressBar.setValue(100)

    # 打开网页控制台
    def open_web(self):
        url = self.ssh_ip.split(':')[0]
        self.ui.browser = QWebEngineView()
        self.ui.browser.setWindowTitle('设备控制台')
        self.ui.browser.setWindowIcon(QIcon("icon.ico"))
        self.ui.browser.load(QUrl('http://'+url))
        self.ui.browser.resize(1280, 720)
        if self.isConnected is True:
            self.ui.browser.show()
        else:
            self.ui.browser.close()

    # 创建左侧列表树右键菜单函数
    def tree_right(self):
        if not self.isConnected:
            # 菜单对象
            self.ui.tree_menu = QMenu(self)
            # 创建菜单选项对象
            self.ui.action = QAction('添加配置', self)
            self.ui.action2 = QAction('删除配置', self)
            # 把动作选项对象添加到菜单self.groupBox_menu上
            self.ui.tree_menu.addAction(self.ui.action)
            self.ui.tree_menu.addAction(self.ui.action2)
            # 将动作A触发时连接到槽函数 button
            self.ui.action.triggered.connect(self.show_addconfig)
            self.ui.action2.triggered.connect(self.del_conf)
            # 声明当鼠标在groupBox控件上右击时，在鼠标位置显示右键菜单   ,exec_,popup两个都可以，
            self.ui.tree_menu.popup(QCursor.pos())
        elif self.isConnected:
            self.ui.tree_menu = QMenu(self)
            self.ui.action = QAction('下载文件', self)
            self.ui.action2 = QAction('上传文件', self)
            self.ui.action3 = QAction('编辑文本', self)
            self.ui.tree_menu.addAction(self.ui.action)
            self.ui.tree_menu.addAction(self.ui.action2)
            self.ui.tree_menu.addAction(self.ui.action3)
            self.ui.action.triggered.connect(self.download_file)
            self.ui.action2.triggered.connect(self.upload_file)
            self.ui.action3.triggered.connect(self.edit_file)
            # 声明当鼠标在groupBox控件上右击时，在鼠标位置显示右键菜单   ,exec_,popup两个都可以，
            self.ui.tree_menu.popup(QCursor.pos())

    # 打开增加配置界面
    def show_addconfig(self):
        self.ui.addconfwin = AddConigUi()
        self.ui.addconfwin.show()
        self.ui.addconfwin.dial.pushButton.clicked.connect(self.refresh_conf)
        self.ui.addconfwin.dial.pushButton_2.clicked.connect(self.ui.addconfwin.close)

    # 刷新设备列表
    def refresh_conf(self):
        if not os.path.exists('config.dat'):
            with open('config.dat', 'wb') as c:
                start_dic = {}
                c.write(pickle.dumps(start_dic))
                c.close()
        with open('config.dat', 'rb') as c:
            dic = pickle.loads(c.read())
            c.close()
        i = 0
        self.ui.treeWidget.clear()
        self.ui.treeWidget.headerItem().setText(0, '设备列表')
        for k in dic.keys():
            self.ui.treeWidget.addTopLevelItem(QTreeWidgetItem(0))
            self.ui.treeWidget.topLevelItem(i).setText(0, k)
            i += 1

    # 当前目录列表刷新
    def refresh_dirs(self):
        self.pwd, files = self.get_dir_now()
        self.dir_tree_now = files[1:]
        self.ui.treeWidget.clear()
        self.ui.treeWidget.headerItem().setText(0, '当前目录：'+self.pwd)
        i = 0
        for n in files[1:]:
            if n[0].startswith('d'):
                self.ui.treeWidget.addTopLevelItem(QTreeWidgetItem(0))
                self.ui.treeWidget.topLevelItem(i).setText(0, n[8])
                self.ui.treeWidget.topLevelItem(i).setIcon(0, QIcon("./ui/image/folder.jpg"))
            elif n[0][0] in ['l', '-', 's']:
                self.ui.treeWidget.addTopLevelItem(QTreeWidgetItem(0))
                self.ui.treeWidget.topLevelItem(i).setText(0, n[8])
                self.ui.treeWidget.topLevelItem(i).setIcon(0, QIcon("./ui/image/file.jpg"))
            i += 1

    # 获取当前目录列表
    def get_dir_now(self):
        pwd = self.get_data2('cd '+self.pwd+' && sudo pwd')
        dir_info = self.get_data2(cmd='cd '+self.pwd+' && sudo ls -al').split('\n')
        dir_n_info = []
        for d in dir_info:
            d_list = get_running_data.DevicInfo.del_more_space(d)
            if d_list:
                dir_n_info.append(d_list)
            else:
                pass
        return pwd[:-1], dir_n_info

    # 打开文件编辑窗口
    def edit_file(self):
        focus = self.ui.treeWidget.currentIndex().row()
        if focus != -1 and self.dir_tree_now[focus][0].startswith('-'):
            self.file_name = self.ui.treeWidget.currentItem().text(0)
            text = self.get_data2('sudo cat '+self.pwd+'/'+self.file_name)
            if text != 'error' and text != '\n':
                self.ui.addTextEditWin = TextEditor(title=self.file_name, old_text=text)
                self.ui.addTextEditWin.show()
                self.ui.addTextEditWin.save_tex.connect(self.get_new_text)
            elif text == 'error' or text == '\n':
                self.alarm('无法编辑文件，请确认！')
        else:
            self.alarm('文件夹不能被编辑！')

    # 获取返回信息，并保存文件
    def get_new_text(self, new_list):
        nt, sig = new_list[0], new_list[1]
        if sig == 0:
            self.get_data2('sudo echo -e "'+nt+'" > '+self.pwd+'/'+self.file_name)
            self.ui.addTextEditWin.new_text = self.ui.addTextEditWin.old_text
            self.ui.addTextEditWin.te.chk.close()
            self.ui.addTextEditWin.close()
        elif sig == 1:
            self.get_data2('sudo echo -e "' + nt + '" > ' + self.pwd + '/' + self.file_name)
            self.ui.addTextEditWin.old_text = nt

    # 删除设备配置文件
    def del_conf(self):
        focus = self.ui.treeWidget.currentIndex().row()
        if focus != -1:
            name = self.ui.treeWidget.topLevelItem(focus).text(0)
            with open('config.dat', 'rb') as c:
                conf = pickle.loads(c.read())
                c.close()
            with open('config.dat', 'wb') as c:
                del conf[name]
                c.write(pickle.dumps(conf))
                c.close()
            self.refresh_conf()
        else:
            self.alarm('请选中要删除的配置')

    # 定时刷新设备状态信息
    def flush_sysinfo(self):
        self.timer1 = QTimer()
        self.timer1.start(1000)
        self.timer1.timeout.connect(self.refresh_sysinfo)

    # 刷新设备状态信息功能
    def refresh_sysinfo(self):
        if self.isConnected:
            cpu_use = self.getsysinfo.cpu_use
            mem_use = self.getsysinfo.mem_use
            dissk_use = self.getsysinfo.disk_use
            self.ui.cpuRate.setValue(cpu_use)
            self.ui.memRate.setValue(mem_use)
            self.ui.diskRate.setValue(dissk_use)
        else:
            self.ui.cpuRate.setValue(0)
            self.ui.memRate.setValue(0)
            self.ui.diskRate.setValue(0)

    # 下载文件
    def download_file(self):
        focus = self.ui.treeWidget.currentIndex().row()
        if focus != -1:
            pass
        else:
            pass
        pass

    # 上传文件
    def upload_file(self):
        pass

    # 信息提示窗口
    def alarm(self, alart):
        self.ui.alarmbox = QMessageBox()
        self.ui.alarmbox.setWindowIcon(QIcon("icon.ico"))
        self.ui.alarmbox.setText(alart)
        self.ui.alarmbox.setWindowTitle('错误提示')
        self.ui.alarmbox.show()

    def inputMethodQuery(self, a0):
        print(a0)


# 增加配置逻辑
class AddConigUi(QDialog):

    def __init__(self):
        super().__init__()
        self.dial = add_config.Ui_addConfig()
        self.dial.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))
        self.dial.pushButton.clicked.connect(self.add_dev)

    def add_dev(self):
        name, username, password, ip = self.dial.configName.text(), self.dial.usernamEdit.text(), \
                                       self.dial.passwordEdit.text(), self.dial.ipEdit.text()
        if name == '':
            self.alarm('配置名称不能为空！')
        elif username == '':
            self.alarm('用户名不能为空！')
        elif password == '':
            self.alarm('密码不能为空！')
        elif ip == '':
            self.alarm('ip地址不能为空！')
        else:
            with open('config.dat', 'rb') as c:
                conf = pickle.loads(c.read())
                c.close()
            with open('config.dat', 'wb') as c:
                conf[name] = [username, password, ip]
                c.write(pickle.dumps(conf))
                c.close()
            self.close()

    def alarm(self, alart):
        self.dial.alarmbox = QMessageBox()
        self.dial.alarmbox.setWindowIcon(QIcon("icon.ico"))
        self.dial.alarmbox.setText(alart)
        self.dial.alarmbox.setWindowTitle('错误提示')
        self.dial.alarmbox.show()


# 在线文本编辑
class TextEditor(QMainWindow):
    save_tex = pyqtSignal(list)

    def __init__(self, title: str, old_text: str, parent=None):
        super(QMainWindow, self).__init__(parent)
        self.te = text_editor.Ui_MainWindow()
        self.te.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))
        self.setWindowTitle(title)

        self.old_text = old_text
        self.te.textEdit.setPlainText(old_text)
        self.new_text = self.te.textEdit.toPlainText()

        self.timer1 = None
        self.flush_new_text()

        self.te.action.triggered.connect(lambda: self.saq(1))
        self.te.action_2.triggered.connect(lambda: self.daq(1))

    def flush_new_text(self):
        self.timer1 = QTimer()
        self.timer1.start(100)
        self.timer1.timeout.connect(self.autosave)

    def autosave(self):
        text = self.te.textEdit.toPlainText()
        self.new_text = text

    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.new_text != self.old_text:
            a0.ignore()
            self.te.chk = Confirm()
            self.te.chk.cfm.save.clicked.connect(lambda: self.saq(0))
            self.te.chk.cfm.drop.clicked.connect(lambda: self.daq(0))
            self.te.chk.show()
        else:
            pass

    def saq(self, sig):
        self.save_tex.emit([self.new_text, sig])

    def daq(self, sig):
        if sig == 0:
            self.new_text = self.old_text
            self.te.chk.close()
            self.close()
        elif sig == 1:
            self.close()


# 文本编辑确认框
class Confirm(QDialog):
    def __init__(self):
        super().__init__()
        self.cfm = confirm.Ui_confirm()
        self.cfm.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))


if __name__ == '__main__':
    aiotmin = QApplication(sys.argv)
    aiot_mainDial = MainDialog()
    aiot_mainDial.show()
    aiot_mainDial.refresh_conf()
    sys.exit(aiotmin.exec_())
