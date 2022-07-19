import sys

class LogConverter:

    def __init__(self, fd):
        self.fd = fd
        self.cand_logs = []
        self.output_logs = []
        self.tmprmd_logs = []

    def remove_tmpfile_log(self):
        for line in self.output_logs:
            if line.split(',')[3].split('/')[-1][0] != '.':
                self.tmprmd_logs.append(line)
        print('\n'.join(self.tmprmd_logs))

    def make_log(self, log):
        if log.split(',')[2] == 'write':
            for line in self.cand_logs:
                if log.split(',')[3] == line.split(',')[3] and line.split(',')[2] == 'open' or line.split(',')[2] == 'create':
                    self.cand_logs.remove(line)
                    self.cand_logs.append(log)

        if log.split(',')[2] == 'read':
            for line in self.cand_logs:
                if log.split(',')[3] == line.split(',')[3] and line.split(',')[2] == 'open':
                    self.cand_logs.remove(line)
                    self.cand_logs.append(log)

        if log.split(',')[2] == 'release':
            for line in self.cand_logs:
                if log.split(',')[3] == line.split(',')[3] and line.split(',')[2] == 'create':
                    self.output_logs.append(log.split(',')[0] + ',' + log.split(',')[1] + ',' + 'Created' + ',' + log.split(',')[3])
                    self.cand_logs.remove(line)
                elif log.split(',')[3] == line.split(',')[3] and line.split(',')[2] == 'write':
                    self.output_logs.append(log.split(',')[0] + ',' + log.split(',')[1] + ',' + 'Updated' + ',' + log.split(',')[3])
                    self.cand_logs.remove(line)
                elif log.split(',')[3] == line.split(',')[3] and line.split(',')[2] == 'read':
                    self.output_logs.append(log.split(',')[0] + ',' + log.split(',')[1] + ',' + 'Read' + ',' + log.split(',')[3])
                    self.cand_logs.remove(line)


    def convert(self):
        lines = self.fd.read().splitlines()

        for line in lines:
            if line.split(',')[2] == 'create':
                self.cand_logs.append(line)
            elif line.split(',')[2] == 'open':
                self.cand_logs.append(line)
            elif line.split(',')[2] == 'release':
                self.make_log(line)
            elif line.split(',')[2] == 'write':
                self.make_log(line)
            elif line.split(',')[2] == 'read':
                self.make_log(line)


    # 作成: create -> release
    # 更新: open/create -> write -> release
    # 参照: open -> read -> release
    # １行ずつ確認して，引っかかれば後ろを見る．それを１行ずつ繰り返す．
    # 候補用の配列にフィルタかけたやつを入れて，1行ずつ当たれば消して入れてそろったら作る．


def main():
    args = sys.argv
    fd = open(args[1], 'r')

    log_converter = LogConverter(fd)
    log_converter.convert()
    log_converter.remove_tmpfile_log()
#    log_converter.get_log()

    fd.close()

if __name__ == "__main__":
    main()
