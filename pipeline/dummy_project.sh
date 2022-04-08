#/bin/bash
base_path=$(dirname "$(realpath $0)")
example_path=$base_path/../example

function demo_batch {
    local image_type=$1Image
    # local project_name=dummy_project
    # local project_name=hook_bag
    local project_name=rcup_20220218_pick
    local n_pixel=$2
    python3 $example_path/train_autoencoder.py -pn $project_name -n 1000 -image $image_type
    python3 $example_path/visualize_autoencoder_result.py -pn $project_name -image $image_type
    python3 $example_path/train_lstm.py -pn $project_name -n 6000 -image $image_type
    python3 $example_path/visualize_lstm_result.py -pn $project_name -image $image_type
    python3 $example_path/visualize_train_history.py -pn $project_name
}

demo_batch RGB 224  # must be 112 or 224
