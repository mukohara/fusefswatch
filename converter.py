from transitions import Machine
import sys
import os

converted_logs = []

class StateMachine(object):
        # 状態の定義
    states = [
        {'name': 'create', 'ignore_invalid_triggers': 'True'},
        {'name': 'open', 'ignore_invalid_triggers': 'True'},
        {'name': 'write', 'ignore_invalid_triggers': 'True'},
        {'name': 'read', 'ignore_invalid_triggers': 'True'},
        {'name': 'release', 'ignore_invalid_triggers': 'True'},
        {'name': 'unlink', 'ignore_invalid_triggers': 'True'},
        {'name': 'rename', 'ignore_invalid_triggers': 'True'},
    ]

    def __init__(self, log):
        self.name = log.split(',')[3]
        self.machine = Machine(model=self, states=StateMachine.states, initial=log.split(',')[2], auto_transitions=False, send_event=True)
        # 遷移の定義
        # trigger：遷移の引き金になるイベント、source：トリガーイベントを受ける状態、dest：トリガーイベントを受けた後の状態
        # before：遷移前に実施されるコールバック、after：遷移後に実施されるコールバック
        self.machine.add_transition(trigger='release',     source='create',   dest='release',   after='make_created')
        self.machine.add_transition(trigger='write',       source='open',     dest='write')
        self.machine.add_transition(trigger='write',       source='create',   dest='write')
        self.machine.add_transition(trigger='release',     source='write',    dest='release',   after='make_updated')
        self.machine.add_transition(trigger='read',        source='open',     dest='read')
        self.machine.add_transition(trigger='release',     source='read',     dest='release',   after='make_read')
        self.machine.add_transition(trigger='create',      source='release',  dest='create')
        self.machine.add_transition(trigger='open',        source='release',  dest='open')
        self.machine.add_transition(trigger='unlink',      source='unlink',   dest='unlink',    after='make_remove')
        self.machine.add_transition(trigger='rename',      source='rename',   dest='rename',    after='make_rename_or_move')

        # 状態を管理したいオブジェクトの元となるクラス
        # 遷移時やイベント発生時のアクションがある場合は、当クラスのmethodに記載する
    def make_created(self, event):
        converted_logs.append(event.args[0].split(',')[0] + ',' + event.args[0].split(',')[1] + ',' + 'Create' + ',' + event.args[0].split(',')[3])

    def make_updated(self, event):
        converted_logs.append(event.args[0].split(',')[0] + ',' + event.args[0].split(',')[1] + ',' + 'Update' + ',' + event.args[0].split(',')[3])

    def make_read(self, event):
        converted_logs.append(event.args[0].split(',')[0] + ',' + event.args[0].split(',')[1] + ',' + 'Read' + ',' + event.args[0].split(',')[3])

    def make_remove(self, event):
        converted_logs.append(event.args[0].split(',')[0] + ',' + event.args[0].split(',')[1] + ',' + 'Remove' + ',' + event.args[0].split(',')[3])

    def make_rename_or_move(self, event):
        src = event.args[0].split(',')[3]
        dst = event.args[0].split(',')[4]

        if len(src.split('/')) == len(dst.split('/')):
            converted_logs.append(event.args[0].split(',')[0] + ',' + event.args[0].split(',')[1] + ',' + 'Rename' + ',' + src + ',' + dst)
        else:
            converted_logs.append(event.args[0].split(',')[0] + ',' + event.args[0].split(',')[1] + ',' + 'Move' + ',' + src + ',' + dst)

class MachineManager:
    def __init__(self):
        self.machines = {}

    def make_machine(self, log):
        path = log.split(',')[3]

        if not path in self.machines:
            machine = StateMachine(log)
            new_machine = {path:machine}
            self.machines.update(new_machine)
            return 0;
        return 1;

    def change_state(self, log):
        path = log.split(',')[3]
        event = log.split(',')[2]

        if path in self.machines:
            machine = self.machines[path]
            if event == 'create':
                machine.create(log)
            elif event == 'open':
                machine.open(log)
            elif event == 'write':
                machine.write(log)
            elif event == 'read':
                machine.read(log)
            elif event == 'release':
                machine.release(log)
                del self.machines[path]
            elif event == 'unlink':
                machine.unlink(log)
                del self.machines[path]
            elif event == 'rename':
                machine.rename(log)
                del self.machines[path]

class LogConverter:
    def __init__(self, fd):
        self.fd = fd
        self.machine_mgr = MachineManager()

    def convert(self):
        lines = self.fd.read().splitlines()

        for line in lines:
            event = line.split(',')[2]
            if event == 'create' or event == 'open' or event == 'rename':
                ret = self.machine_mgr.make_machine(line)
                if ret == 0: # if machine is generated
                    pass
                else:
                    self.machine_mgr.change_state(line)
            elif event == 'write' or event == 'read' or event == 'release' or event == 'rename':
                self.machine_mgr.change_state(line)
            elif event == 'unlink':
                self.machine_mgr.make_machine(line)
                self.machine_mgr.change_state(line)

    def remove_tmpfile_log(self, logs):
        procd_logs = []
        for line in logs:
            if line.split(',')[3].split('/')[-1][0] != '.' and line.split(',')[3].split('/')[-1] != '4913':
                procd_logs.append(line)
        return procd_logs

    def search_copy_log(self, logs):
        copy_logs = []
        for idx, line in enumerate(logs):
            prev_event = logs[idx-1].split(',')[2]
            event = line.split(',')[2]
            prev_path = logs[idx-1].split(',')[3]
            path = line.split(',')[3]

            if prev_event == 'Updated' and event == 'Read':
                if os.path.getsize(prev_path) == os.path.getsize(path) and path != prev_path:
                    copy_logs.append(line.split(',')[0] + ',' + 'Copied' + ',' + 'from ' + path + ' to ' + prev_path)
        return copy_logs

    def fix_homedir_path(self, logs):
        procd_logs = []
        for line in logs:
            procd_logs.append(line.replace('mukohara.fuse-watch', 'mukohara'))
        return procd_logs

    def remove_script_log(self, logs):
        procd_logs = []
        for line in logs:
            if line.split(',')[3].split('/')[-1] != 'fuse-watch.sh':
                procd_logs.append(line)
        return procd_logs

    # def remove_duplication(self, logs):
    #     procd_logs = []
    #     for i, line in enumerate(logs):
    #         if :
    #             asd
    #         else:
    #             procd_logs.append(line)

def main():
    args = sys.argv
    fd = open(args[1], 'r', errors='replace')

    log_converter = LogConverter(fd)
    log_converter.convert()

    out_logs_tmprmd = log_converter.remove_tmpfile_log(converted_logs)

    logs_homedir_fixed = log_converter.fix_homedir_path(out_logs_tmprmd)
    logs_scrlog_rmd = log_converter.remove_script_log(logs_homedir_fixed)
    print('logs: ')
    print('\n'.join(logs_scrlog_rmd))

    copy_logs = log_converter.search_copy_log(logs_homedir_fixed)
    print('copy_logs: ')
    print('\n'.join(copy_logs))

    fd.close()

if __name__ == "__main__":
    main()
