import paramiko
import time


class DevicInfo:
    def __init__(self, username, password, host):
        super(DevicInfo, self).__init__()
        self.username, self.password, self.host = username, password, host
        self.cpu_use, self.mem_use, self.disk_use = 0, 0, 0
        self.conn = paramiko.SSHClient()
        self.conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.conn.connect(username=username, password=password, hostname=host.split(':')[0], port=host.split(':')[1])
        self.close_sig = 1

    @staticmethod
    def del_more_space(line: str) -> list:
        l = line.split(' ')
        ln = []
        for ll in l:
            if ll == ' ' or ll == '':
                pass
            elif ll != ' ' and ll != '':
                ln.append(ll)
        return ln

    def cpu_use_data(self, info: str) -> tuple:
        lines = info.split('\n')
        for l in lines:
            if l.startswith('cpu'):
                ll = self.del_more_space(l)
                i = int(ll[1])+int(ll[2])+int(ll[3])+int(ll[4])+int(ll[5])+int(ll[6])+int(ll[7])
                return i, int(ll[4])

    def disk_use_data(self, info: str) -> int:
        lines = info.split('\n')
        for l in lines:
            if l.endswith('/'):
                ll = self.del_more_space(l)
                if len(ll[4]) == 3:
                    return int(ll[4][0:2])
                elif len(ll[4]) == 2:
                    return int(ll[4][0:1])
                elif len(ll[4]) == 4:
                    return int(ll[4][0:3])

    def mem_use_data(self, info: str) -> int:
        lines = info.split('\n')
        for l in lines:
            if l.startswith('Mem'):
                ll = self.del_more_space(l)
                return int((int(ll[2]))/int(ll[1])*100)

    def get_datas(self):
        while True:
            if self.close_sig == 0:
                break
            stdin, stdout, stderr = self.conn.exec_command(timeout=10, bufsize=100, command='sudo cat /proc/stat')
            cpuinfo1 = stdout.read().decode('utf8')
            time.sleep(1)
            stdin, stdout, stderr = self.conn.exec_command(timeout=10, bufsize=100, command='sudo cat /proc/stat')
            cpuinfo2 = stdout.read().decode('utf8')
            stdin, stdout, stderr = self.conn.exec_command(timeout=10, bufsize=100, command='sudo df')
            diskinfo = stdout.read().decode('utf8')
            stdin, stdout, stderr = self.conn.exec_command(timeout=10, bufsize=100, command='sudo free')
            meminfo = stdout.read().decode('utf8')
            c_u1, c_idle1 = self.cpu_use_data(cpuinfo1)
            c_u2, c_idle2 = self.cpu_use_data(cpuinfo2)
            self.cpu_use = int((1-(c_idle2-c_idle1)/(c_u2-c_u1))*100)
            self.mem_use = self.mem_use_data(meminfo)
            self.disk_use = self.disk_use_data(diskinfo)
            time.sleep(1)

    def disconnect(self):
        self.close_sig = 0
        self.conn.close()
