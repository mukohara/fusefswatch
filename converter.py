from transitions import Machine
import sys

out_logs = []
out_logs_tmprmd = []

class StateMachine(object):
        # 状態の定義
    states = [
        {'name': 'create', 'ignore_invalid_triggers': 'True'},
        {'name': 'open', 'ignore_invalid_triggers': 'True'},
        {'name': 'write', 'ignore_invalid_triggers': 'True'},
        {'name': 'read', 'ignore_invalid_triggers': 'True'},
        {'name': 'release', 'ignore_invalid_triggers': 'True'},
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

        # 状態を管理したいオブジェクトの元となるクラス
        # 遷移時やイベント発生時のアクションがある場合は、当クラスのmethodに記載する
    def make_created(self, event):
        out_logs.append(event.args[0].split(',')[0] + ',' + event.args[0].split(',')[1] + ',' + 'Created' + ',' + event.args[0].split(',')[3])

    def make_updated(self, event):
        out_logs.append(event.args[0].split(',')[0] + ',' + event.args[0].split(',')[1] + ',' + 'Updated' + ',' + event.args[0].split(',')[3])

    def make_read(self, event):
        out_logs.append(event.args[0].split(',')[0] + ',' + event.args[0].split(',')[1] + ',' + 'Read' + ',' + event.args[0].split(',')[3])

class MachineManager:
    def __init__(self):
        self.machines = {}

    def make_machine(self, log):
        path = log.split(',')[3]

        if not path in self.machines:
            machine = StateMachine(log)
            new_machine = {path:machine}
            self.machines.update(new_machine)

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
class LogConverter:
    def __init__(self, fd):
        self.fd = fd
        self.machine_mgr = MachineManager()

    def convert(self):
        lines = self.fd.read().splitlines()

        for line in lines:
            event = line.split(',')[2]
            if event == 'create' or event == 'open':
                self.machine_mgr.make_machine(line)

            if event == 'create' or event == 'open' or event == 'write' or event == 'read' or event == 'release':
                self.machine_mgr.change_state(line)

    def remove_tmpfile_log(self):
        for line in out_logs:
            if line.split(',')[3].split('/')[-1][0] != '.':
                out_logs_tmprmd.append(line)

def main():
    args = sys.argv
    fd = open(args[1], 'r', errors='replace')

    log_converter = LogConverter(fd)
    log_converter.convert()
    print('out_logs: ')
    print('\n'.join(out_logs))
    log_converter.remove_tmpfile_log()
    print('out_logs_tmprmd: ')
    print('\n'.join(out_logs_tmprmd))


    fd.close()

if __name__ == "__main__":
    main()
