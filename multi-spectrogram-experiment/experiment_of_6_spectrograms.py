# -*- coding: utf-8 -*-
"""first-1-copy-experiment-of-6-spectrograms.ipynb
 *   Mounts Google Drive and creates directories for saving datasets and models.


 *   Loads the NSynth dataset and prepares spectrogram data for each instrument family.
 *   Defines functions to convert audio to spectrograms, augment datasets with negative examples, create models, and clear GPU memory.
 *   Prepares N samples for each instrument family, ensuring balance by repeating existing samples if necessary.
 *   Trains binary classifiers for each instrument family using different spectrogram types and saves the trained models and training metrics.
 *   Each spectrogram type (STFT, Log-Mel, MFCC, Chroma, Spectral Contrast, Tonnetz) will have its own directory with models and training metrics saved separately.
"""

import tensorflow as tf
import numpy as np
import os
import matplotlib.pyplot as plt
from tensorflow.keras.backend import clear_session
from google.colab import drive
import gc
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

"""Mount google drive"""

# Mount Google Drive
drive.mount('/content/drive')

"""define the global vars"""

# Directory paths
base_dir = '/content/drive/My Drive/200-each-instrument/'
combined_save_dir = os.path.join(base_dir, 'all_combined_with_padding')

# New base directory for saving models and metrics
output_dir = '/content/drive/My Drive/output-multi-gram/'

"""load data

"""

# Instrument families
instrument_families = ['bass', 'brass', 'flute', 'guitar', 'keyboard', 'mallet', 'organ', 'reed', 'string', 'vocal']

# Spectrogram types ['stft', 'log_mel', 'mfcc', 'chroma', 'spectral_contrast', 'tonnetz', 'all_combined_with_padding']
spectrogram_types = ['stft', 'log_mel', 'mfcc', 'chroma', 'spectral_contrast', 'tonnetz', 'all_combined_with_padding']

def load_data(family, spectrogram_type=None):
    if spectrogram_type:
      if spectrogram_type !="all_combined_with_padding":
        file_path = os.path.join(base_dir, spectrogram_type, family, f'{family}_{spectrogram_type}.npy')
      else:
        file_path = os.path.join(combined_save_dir, f'{family}_combined.npy')
    else:
        file_path = os.path.join(base_dir, f'{family}.npy')
    return np.load(file_path)

def create_model(input_shape):
    model = tf.keras.Sequential([
        tf.keras.layers.InputLayer(input_shape=input_shape),
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Dropout(0.25),

        tf.keras.layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Dropout(0.25),

        tf.keras.layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        tf.keras.layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Dropout(0.25),

        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

# Function to clear GPU memory
def clear_gpu_memory(*args):
    del args
    gc.collect()
    clear_session()

# Training function
def train_model_for_spectrogram_type(spectrogram_type, instrument_families):
    print(f"Training for spectrogram type: {spectrogram_type}")
    models_dir = os.path.join(output_dir, 'models', spectrogram_type)
    metrics_dir = os.path.join(output_dir, 'metrics', spectrogram_type)
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(metrics_dir, exist_ok=True)

    for family in instrument_families:
        print(f"Training model for {family}")
        x_positive = load_data(family, spectrogram_type)[:150]
        y_positive = np.ones(x_positive.shape[0])

        x_negative = []
        for other_family in instrument_families:
            if other_family != family:
                x_neg = load_data(other_family, spectrogram_type)[:150]
                x_negative.append(x_neg)
        x_negative = np.vstack(x_negative)
        y_negative = np.zeros(x_negative.shape[0])

        x_train = np.vstack((x_positive, x_negative))
        y_train = np.concatenate((y_positive, y_negative))

        # Expand dimensions to match the expected input shape for Conv2D
        x_train = np.expand_dims(x_train, axis=-1)

        model = create_model(input_shape=x_train[0].shape)

        # Assuming `model` is already defined and compiled
        # Adjust patience for early stopping and learning rate reduction
        early_stopping = EarlyStopping(monitor='val_loss', patience=300, restore_best_weights=True)
        reduce_lr = ReduceLROnPlateau(monitor='val_loss', patience=150, factor=0.5, min_lr=1e-7)

        history = model.fit(x_train, y_train, validation_split=0.3, epochs=1000, callbacks=[early_stopping, reduce_lr])
        model_save_path = os.path.join(models_dir, f'{spectrogram_type}_{family}.h5')
        model.save(model_save_path)

        loss_file_path = os.path.join(metrics_dir, f'{spectrogram_type}_{family}_loss_curve.txt')
        acc_file_path = os.path.join(metrics_dir, f'{spectrogram_type}_{family}_acc_curve.txt')

        with open(loss_file_path, 'w') as f_loss, open(acc_file_path, 'w') as f_acc:
            for loss, acc in zip(history.history['loss'], history.history['accuracy']):
                f_loss.write(f"{loss}\n")
                f_acc.write(f"{acc}\n")

        clear_gpu_memory(x_train, y_train)

# Train and save models for each spectrogram type
for spectrogram_type in spectrogram_types:
    train_model_for_spectrogram_type(spectrogram_type, instrument_families)

print("Training completed and models saved.")
