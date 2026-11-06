#!/usr/bin/env bash
# Fetches the week-2 datasets and weights into ./data-cache (override with the env vars the scripts read).
set -euo pipefail
D=${DATA:-$PWD/data-cache}; mkdir -p "$D"
# CIFAR-10, binary version (Krizhevsky 2009), checked against the SHA-256 values in data/cifar10_sha256.txt
if [ ! -f "$D/cifar/test_batch.bin" ]; then
  curl -L https://www.cs.toronto.edu/~kriz/cifar-10-binary.tar.gz | tar xz -C "$D" && mv "$D/cifar-10-batches-bin" "$D/cifar"
  (cd "$D/cifar" && sha256sum -c "$OLDPWD/data/cifar10_sha256.txt")
fi
# PlantVillage (Hughes & Salathé 2015): only the 3,971 tomato images used here, via a blob-less sparse clone
if [ ! -d "$D/pv/raw/color" ]; then
  git clone --filter=blob:none --no-checkout https://github.com/spMohanty/PlantVillage-Dataset "$D/pv"
  (cd "$D/pv" && git sparse-checkout set --no-cone --stdin < "$OLDPWD/data/plantvillage_files.txt" && git checkout master)
fi
# Official Keras ImageNet weights (no top)
curl -L -o "$D/resnet50_notop.h5" -C - https://github.com/fchollet/deep-learning-models/releases/download/v0.2/resnet50_weights_tf_dim_ordering_tf_kernels_notop.h5
curl -L -o "$D/mobilenetv2_notop.h5" -C - https://github.com/JonathanCMitchell/mobilenet_v2_keras/releases/download/v1.1/mobilenet_v2_weights_tf_dim_ordering_tf_kernels_1.0_224_no_top.h5
echo "export CIFAR_DIR=$D/cifar PLANT_DIR=$D/pv/raw/color RESNET_WEIGHTS=$D/resnet50_notop.h5 MNV2_WEIGHTS=$D/mobilenetv2_notop.h5"
