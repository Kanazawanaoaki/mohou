### mohou [![CI](https://github.com/HiroIshida/mohou/actions/workflows/test.yaml/badge.svg)](https://github.com/HiroIshida/mohou/actions)

This package implements imitation learning trainer and executor using pytorch. Currently the library targets autoencoder-lstm-type behavior cloning.

### Tutorial demo
Running [`pipeline/demo.sh`](/pipeline/demo.sh) is a good first step.

A key concept of this library is a "project", where any data, learned models, result visualizations and logs are stored in `~/.mohou/{project_name}/MultiEpisodeChunk.pkl`. Thanks to this project-based data management, we are free from hard-coding file paths.

- `kuka_reaching.py` creates `MultiEpisodeChunk.pkl` which consists of `n` sample trajectories that reaches to the box in the image (stored in `~/.mohou/{project_name}/). The datachunk consists of sequences of `RGBImage` and `DepthImage` and `AngleVector`. Also, one of the trajectory image in the chunk is visualized as `~/.mohou/{project_name}/sample.gif`.

- `train_autoencoder.py` trains an autoencoder of `$image_type`. $image_type can either be `RGBImange`, `DepthImage` or `RGBDImage`. The train cache is stored as `~/.mohou/{project_name}/TrainCache-AutoEncoder.pkl`.

- `visualize_autoencoder_result.py` visualize the comparison of original and reconstructed image by the autoencoder (stored in `~/.mohou/{project_name}/autoencoder_result/)`. This visualization is useful for debugging/tunning, especially to determine the train epoch of autoencoder if needed.

- `train_lstm.py` trains and lstm that propagate vectors concated by feature vector compressed by the trained autoencoder and `AngleVector`. Note that `train_autoencoder.py` must be run beforehand. The train cache is stored as `~/.mohou/{project_name}/TrainCache-LSTM.pkl`.

- `visualize_lstm_result.py` visualizes the `n` step prediction given 10 images, which can be used for debugging/tuning or determining the good training epoch of the lstm training. The gif file is stored as `~/.mohou/{project_name}/lstm_result/result.gif`

- `visualize_train_history.py` visualizes the training history (test and validation loss) for all train caches in the project directry. The figures will be stored in `~/.mohou/{project_name}/train_history/`

- `kuka_reaching.py --fedback` simualte the visuo-motor reaching task in the simulator using trained autoencoder and lstm. The visualization of the simulation is stored as `~/.mohou/{project_name}/feedback_simulation.gif`.

Also note that logs by `train_autoencoder.py` and `train_lstm.py` will be stored in `~/.mohou/{project_name}/log/`.

For example, after running `demo_batch Depth` in [`pipeline/demo.sh`](/pipeline/demo.sh), we can confirm that following directly sturecture under the corresponding project directry.

```
h-ishida@bc89d7233948:~$ tree ~/.mohou/pipeline_test_Depth/
/home/h-ishida/.mohou/pipeline_test_Depth/
├── MultiEpisodeChunk.pkl
├── TrainCache-AutoEncoder.pkl
├── TrainCache-LSTM.pkl
├── autoencoder_result
│   ├── result0.png
│   ├── result1.png
│   ├── result2.png
│   ├── result3.png
│   └── result4.png
├── feedback_simulation.gif
├── log
│   ├── autoencoder_20220227012024.log
│   ├── latest_autoencoder.log -> /home/h-ishida/.mohou/pipeline_test_Depth/log/autoencoder_20220227012024.log
│   ├── latest_lstm.log -> /home/h-ishida/.mohou/pipeline_test_Depth/log/lstm_20220227025009.log
│   └── lstm_20220227025009.log
├── lstm_result
│   └── result.gif
├── sample.gif
└── train_history
    ├── TrainCache-AutoEncoder.pkl.png
    └── TrainCache-LSTM.pkl.png
```
