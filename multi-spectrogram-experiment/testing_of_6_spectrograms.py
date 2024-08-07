# -*- coding: utf-8 -*-
"""validation-of-6-spectrograms.ipynb

Validation

1. Load the prepared data for validation.
2. Extract the last 50 samples for each instrument family from each spectrogram type.
3. Combine these samples into a single validation dataset.
4. Map the true labels back to the NSynth dataset labels, excluding "synth_lead."
5. Perform validation and save the results.
6. Adapted Validation Code
"""

import tensorflow as tf
import numpy as np
import os
from google.colab import drive
from tensorflow.keras.models import load_model
from sklearn.metrics import classification_report, confusion_matrix
import cv2  # Import OpenCV for resizing

"""Mount google drive"""

# Mount Google Drive
drive.mount('/content/drive')

"""Need to generate the polyphony samples

define the global vars
"""

# Directory paths
base_dir = '/content/drive/My Drive/200-each-instrument/'
combined_save_dir = os.path.join(base_dir, 'all_combined_with_padding')
output_dir = '/content/drive/My Drive/output-multi-gram/'
models_dir = os.path.join(output_dir, 'models')
metrics_dir = os.path.join(output_dir, 'metrics')
test_results_dir = os.path.join(output_dir, 'test_results')

os.makedirs(test_results_dir, exist_ok=True)

"""load data

"""

# Instrument families and their original NSynth labels
instrument_families = {
    'bass': 0,
    'brass': 1,
    'flute': 2,
    'guitar': 3,
    'keyboard': 4,
    'mallet': 5,
    'organ': 6,
    'reed': 7,
    'string': 8,
    #'synth_lead' : 9, missing from tensorflow dataset
    'vocal': 10
}

# Spectrogram types
spectrogram_types = ['stft', 'log_mel', 'mfcc', 'chroma', 'spectral_contrast', 'tonnetz', 'all_combined_with_padding']

# Load data function
def load_data(family, spectrogram_type=None):
    if spectrogram_type:
        if spectrogram_type != "all_combined_with_padding":
            file_path = os.path.join(base_dir, spectrogram_type, family, f'{family}_{spectrogram_type}.npy')
        else:
            file_path = os.path.join(combined_save_dir, f'{family}_combined.npy')
    else:
        file_path = os.path.join(base_dir, f'{family}.npy')
    return np.load(file_path)

"""load models"""

# Instrument families and their original NSynth labels
instrument_families = {
    'bass': 0,
    'brass': 1,
    'flute': 2,
    'guitar': 3,
    'keyboard': 4,
    'mallet': 5,
    'organ': 6,
    'reed': 7,
    'string': 8,
    #'synth_lead' : 9, missing from tensorflow dataset
    'vocal': 9  # Adjusted index to 9 since 'synth_lead' is missing
}

# Spectrogram types
spectrogram_types = ['stft', 'log_mel', 'mfcc', 'chroma', 'spectral_contrast', 'tonnetz', 'all_combined_with_padding']

# Load data function
def load_data(family, spectrogram_type=None):
    if spectrogram_type:
        if spectrogram_type != "all_combined_with_padding":
            file_path = os.path.join(base_dir, spectrogram_type, family, f'{family}_{spectrogram_type}.npy')
        else:
            file_path = os.path.join(combined_save_dir, f'{family}_combined.npy')
    else:
        file_path = os.path.join(base_dir, f'{family}.npy')
    return np.load(file_path)


# Load models function
def load_models(spectrogram_type):
    model_cache = {}
    for family in instrument_families:
        model_path = os.path.join(models_dir, spectrogram_type, f'{spectrogram_type}_{family}.h5')
        model_cache[family] = load_model(model_path)
    return model_cache

# Function to resize spectrograms
def resize_spectrogram(spectrogram, target_shape):
    return cv2.resize(spectrogram, target_shape, interpolation=cv2.INTER_CUBIC)

"""validation"""

# Validation function
def validate_and_save_results(spectrogram_type, model_cache):
    x_val = []
    y_val = []

    for family, label in instrument_families.items():
        data_check = load_data(family, spectrogram_type)[:1] # check the first training sample size
        data = load_data(family, spectrogram_type)[-50:]  # Get the last 50 samples
        if data[0].shape != data_check[0].shape:
            # 6(spetrogram)+1(all_combined) * 10(instrument) = 70(senario) so need to debug if there is a mistake while we generate the data
            print(f"Resizing required for {spectrogram_type}, {family}, index: 0")
            print(f"Training shape: {data_check[0].shape}, Testing shape: {data[0].shape}")

            target_shape = data_check[0].shape
            resized_data = np.array([resize_spectrogram(s, target_shape) for s in data])

        else:
            resized_data = data
        x_val.append(resized_data)
        y_val.extend([label] * len(resized_data))

    x_val = np.concatenate(x_val, axis=0)
    y_val = np.array(y_val)

    x_val = np.expand_dims(x_val, axis=-1)

    y_pred = np.zeros((x_val.shape[0], len(instrument_families)))
    for family, label in instrument_families.items():
        y_pred[:, label] = model_cache[family].predict(x_val).flatten()

    y_pred_labels = np.argmax(y_pred, axis=1)

    true_label_path = os.path.join(test_results_dir, f'{spectrogram_type}_true_labels.txt')
    predicted_labels_path = os.path.join(test_results_dir, f'{spectrogram_type}_predicted_labels.txt')

    np.savetxt(true_label_path, y_val, fmt='%d')
    np.savetxt(predicted_labels_path, y_pred_labels, fmt='%d')

    print(f"True labels saved to: {true_label_path}")
    print(f"Predicted labels saved to: {predicted_labels_path}")

    print(f"\nClassification Report for {spectrogram_type}:")
    print(classification_report(y_val, y_pred_labels, target_names=list(instrument_families.keys())))

    conf_matrix = confusion_matrix(y_val, y_pred_labels)
    print(f"Confusion Matrix for {spectrogram_type}:\n{conf_matrix}")

# Main validation loop for all spectrogram types
for spectrogram_type in spectrogram_types:
    model_cache = load_models(spectrogram_type)
    validate_and_save_results(spectrogram_type, model_cache)

print("Validation completed and results saved.")

"""plot"""

import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.gridspec import GridSpec

# Directory paths
base_dir = '/content/drive/My Drive/200-each-instrument/'
output_dir = '/content/drive/My Drive/output-multi-gram/'
metrics_dir = os.path.join(output_dir, 'metrics')

# Instrument families and their original NSynth labels
instrument_families = ['bass', 'brass', 'flute', 'guitar', 'keyboard', 'mallet', 'organ', 'reed', 'string', 'vocal']

# Spectrogram types
spectrogram_types = ['stft', 'log_mel', 'mfcc', 'chroma', 'spectral_contrast', 'tonnetz', 'all_combined_with_padding']

# Function to read data from a text file
def read_data(file_path):
    with open(file_path, 'r') as file:
        data = file.read().splitlines()
    return np.array(data, dtype=float)

def format_label(label):
    # Replace underscores with spaces
    label = label.replace('_', ' ')
    # Capitalize the first letter of each word
    formatted_label = label.title()
    return formatted_label

# Function to plot and save training curves for a specific instrument
def plot_training_curves(instrument):
    num_plots = len(spectrogram_types) * 2  # Two plots per spectrogram type (loss and accuracy)
    num_cols = 4  # Four plots per row
    num_rows = (num_plots + num_cols - 1) // num_cols  # Calculate the number of rows needed

    fig = plt.figure(figsize=(20, 4 * num_rows))
    fig.suptitle(f'Training Curves for {instrument.title()}', fontsize=16, y=1.00)
    gs = GridSpec(num_rows, num_cols, figure=fig)

    plot_index = 0

    for i, spectrogram_type in enumerate(spectrogram_types):
        loss_file = os.path.join(metrics_dir, spectrogram_type, f'{spectrogram_type}_{instrument}_loss_curve.txt')
        acc_file = os.path.join(metrics_dir, spectrogram_type, f'{spectrogram_type}_{instrument}_acc_curve.txt')

        if spectrogram_type == 'all_combined_with_padding':
            row, col = divmod(plot_index, num_cols)
            ax_loss = fig.add_subplot(gs[row, col:col+2])
            ax_acc = fig.add_subplot(gs[row, col+2:col+4])
            plot_index += 4  # Skip next 4 cells
        else:
            row, col = divmod(plot_index, num_cols)
            ax_loss = fig.add_subplot(gs[row, col])
            ax_acc = fig.add_subplot(gs[row, col + 1])
            plot_index += 2  # Skip next 2 cells

        if os.path.exists(loss_file) and os.path.exists(acc_file):
            loss_data = read_data(loss_file)
            acc_data = read_data(acc_file)

            ax_loss.plot(loss_data)
            ax_loss.set_title(f'{spectrogram_type} Loss Curve')
            ax_loss.set_xlabel('Epochs')
            ax_loss.set_ylabel('Loss')

            ax_acc.plot(acc_data)
            ax_acc.set_title(f'{spectrogram_type} Accuracy Curve')
            ax_acc.set_xlabel('Epochs')
            ax_acc.set_ylabel('Accuracy')
        else:
            ax_loss.text(0.5, 0.5, 'File Not Found', horizontalalignment='center', verticalalignment='center', transform=ax_loss.transAxes)
            ax_acc.text(0.5, 0.5, 'File Not Found', horizontalalignment='center', verticalalignment='center', transform=ax_acc.transAxes)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust layout to make space for the title
    plt.subplots_adjust(top=0.95)  # Increase space above the subplots
    plt.savefig(os.path.join(metrics_dir, f'{instrument}_training_curves.png'))
    plt.show()

# Plot and save training curves for each instrument
for instrument in instrument_families:
    plot_training_curves(instrument)

print("Plotting and saving of training curves completed.")
