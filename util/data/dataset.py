import torch
from torch.utils.data import Dataset
from util.common_util import (splice_path)


def load_label_vocab(label_path):
    with open(label_path, encoding="utf-8") as f:
        res = [i.strip().lower() for i in f.readlines() if len(i.strip()) != 0]
    return res, dict(zip(res, range(len(res)))), dict(zip(range(len(res)), res))  # list, token2index, index2token


class THUCNewsDataset(Dataset):
    """
        THUCNews 新闻数据集的数据处理里类
    """

    def __init__(self, args, path, tokenizer, logger):
        """
            args: 数据加载的基本参数
            path: 数据的源路径
            tokenizer: 分词器
            logger: 日志处理对象
            max_lengths: 序列的最大长度 默认：2048

        """
        super(THUCNewsDataset, self).__init__()
        self.tokenizer = tokenizer
        self.config = args
        self.logger = logger
        _, self.label_vocal, _ = load_label_vocab(splice_path(args.data_root, args.label_path))
        self.path = splice_path(args.data_root, path)
        self.data = THUCNewsDataset.data_processor(path=self.path,
                                                   tokenizer=tokenizer,
                                                   max_length=self.config.max_length,
                                                   logger = logger)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        label_vocab, sent_token, attention_mask = self.data[item]
        return {'label': label_vocab, 'sent_token': sent_token, 'attention_mask': attention_mask}

    @staticmethod
    def data_processor(path, tokenizer, max_length, logger):
        dataset = []
        logger.info('Reading data from {}'.format(path))
        with open(path, 'r', encoding="utf-8") as file:
            lines = [line.strip().split(",", 1) for line in file.readlines() if len(line.strip()) != 0]
            for label, text in lines:
                sent_token = tokenizer(text[:max_length])
                dataset.append([int(label)-1,
                                sent_token['input_ids'],
                                sent_token['attention_mask']])

        logger.info('{} data record loaded'.format(len(dataset)))
        return dataset


class PadTHUCNewsSeqFn:
    def __init__(self, pad_idx):
        self.pad_idx = pad_idx

    def __call__(self, batch):
        res = dict()
        res['label'] = torch.tensor([i['label'] for i in batch]).long()
        max_len = max([len(i['sent_token']) for i in batch])
        res['sent_token'] = torch.tensor([i['sent_token'] +
                                          [self.pad_idx] * (max_len - len(i['sent_token']))
                                          for i in batch]).long()

        res['attention_mask'] = torch.tensor([i['attention_mask'] +
                                              [self.pad_idx] * (max_len - len(i['attention_mask']))
                                              for i in batch]).long()
        return res



