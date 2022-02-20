import argparse

from mohou.model.lstm import LSTMConfig
from mohou.trainer import TrainCache, TrainConfig, train
from mohou.types import MultiEpisodeChunk
from mohou.types import AngleVector
from mohou.model import AutoEncoder, LSTM
from mohou.dataset import AutoRegressiveDataset
from mohou.embedding_functor import IdenticalEmbeddingFunctor
from mohou.embedding_rule import RGBAngelVectorEmbeddingRule
from mohou.utils import detect_device, split_with_ratio

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-pn', type=str, default='kuka_reaching', help='project name')
    parser.add_argument('-n', type=int, default=3000, help='iteration number')
    parser.add_argument('-valid-ratio', type=float, default=0.1, help='split rate for validation dataset')
    args = parser.parse_args()

    project_name = args.pn
    n_epoch = args.n
    valid_ratio = args.valid_ratio

    chunk = MultiEpisodeChunk.load(project_name)

    tcache_autoencoder = TrainCache.load(project_name, AutoEncoder)
    image_embed_func = tcache_autoencoder.best_model.get_embedding_functor()

    av_idendical_func = IdenticalEmbeddingFunctor(chunk.get_element_shape(AngleVector)[0])
    embed_rule = RGBAngelVectorEmbeddingRule(image_embed_func, av_idendical_func)

    dataset = AutoRegressiveDataset.from_chunk(chunk, embed_rule)
    dataset_train, dataset_valid = split_with_ratio(dataset, valid_ratio=valid_ratio)

    lstm_model = LSTM(detect_device(), LSTMConfig(embed_rule.dimension))

    tconfig = TrainConfig(n_epoch=3)
    tcache = TrainCache[LSTM](project_name)
    train(lstm_model, dataset_train, dataset_valid, tcache, config=tconfig)
