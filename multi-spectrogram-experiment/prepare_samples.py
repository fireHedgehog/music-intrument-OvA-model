# -*- coding: utf-8 -*-
"""prepare-samples.ipynb
"""

import numpy as np
import os
from google.colab import drive
import librosa
import tensorflow_datasets as tfds
import cv2

"""mount disk"""

# Mount Google Drive
drive.mount('/content/drive')

# Create directory for saving the datasets
save_dir = '/content/drive/My Drive/200-each-instrument/'
os.makedirs(save_dir, exist_ok=True)

# Instrument family mapping
label_map_10 = {
    0: 'bass',
    1: 'brass',
    2: 'flute',
    3: 'guitar',
    4: 'keyboard',
    5: 'mallet',
    6: 'organ',
    7: 'reed',
    8: 'string',
    10: 'vocal',
}
instrument_families = ['bass', 'brass', 'flute', 'guitar', 'keyboard', 'mallet', 'organ', 'reed', 'string', 'vocal']

# Dictionary to store data for each instrument family data_dict = {'bass': [], 'brass': [], 'flute': [], 'guitar': [], 'keyboard': [], 'mallet': [],
#'organ': [], 'reed': [], 'string': [], 'synth_lead': [], 'vocal': []}
data_dict = {label: [] for label in label_map_10.values()}

"""download 70GiB dataset"""

# Load NSynth dataset
ds = tfds.load('nsynth', split='train+test+valid')

"""store samples"""

# Dictionary to store data for each instrument family
data_dict = {label: [] for label in label_map_10.values()}

# Iterate through the dataset and separate data by instrument family
sample_limit = 200
for example in ds:
    family_label = example['instrument']['family'].numpy()
    if family_label in label_map_10:
        instrument_family = label_map_10[family_label]
        if len(data_dict[instrument_family]) < sample_limit:
            audio = example['audio'].numpy()
            data_dict[instrument_family].append(audio)

    # Stop if we have enough samples for each family
    if all(len(data) >= sample_limit for data in data_dict.values()):
        break

# Ensure each family has 200 samples by repeating samples if necessary
for family, data in data_dict.items():
    if len(data) < 200:
        data = data * (200 // len(data)) + data[:200 % len(data)]
    data_dict[family] = np.array(data[:200])
    # np.save(os.path.join(save_dir, f'{family}.npy'), data_dict[family])

print(f"Data for each instrument family has been saved to {save_dir}")

"""save spectrograms"""

# Function to normalize data
def normalize_data(data):
    data = np.nan_to_num(data)  # Replace NaNs with zero
    mean = np.mean(data)
    std = np.std(data)
    if std == 0:
        std = 1
    return (data - mean) / std

# Function to resize spectrograms
def resize_spectrogram(spectrogram, target_height):
    return cv2.resize(spectrogram, (spectrogram.shape[1], target_height), interpolation=cv2.INTER_LINEAR)

# Function to check for NaNs or infinite values
def check_nan_inf(data):
    if np.isnan(data).any() or np.isinf(data).any():
        print("Data contains NaN or infinite values")
    else:
        print("Data is clean")

# Define functions to convert audio to various spectrograms
def audio_to_spectrogram(audio_sample, sr=16000, n_fft=2048, hop_length=512):
    spectrogram = librosa.stft(audio_sample, n_fft=n_fft, hop_length=hop_length)
    spectrogram_db = librosa.amplitude_to_db(abs(spectrogram))
    return spectrogram_db

def audio_to_log_mel_spectrogram(audio_sample, sr=16000, n_fft=2048, hop_length=512, n_mels=256):
    mel_spectrogram = librosa.feature.melspectrogram(y=audio_sample, sr=sr, n_fft=n_fft, hop_length=hop_length, n_mels=n_mels)
    log_mel_spectrogram = librosa.power_to_db(mel_spectrogram)
    return log_mel_spectrogram

def audio_to_mfcc(audio_sample, sr=16000, n_mfcc=60, n_fft=2048, hop_length=512):
    mfcc = librosa.feature.mfcc(y=audio_sample, sr=sr, n_mfcc=n_mfcc, n_fft=n_fft, hop_length=hop_length)
    return mfcc

def audio_to_chroma(audio_sample, sr=16000, n_fft=2048, hop_length=512, n_chroma=64):
    chroma = librosa.feature.chroma_stft(y=audio_sample, sr=sr, n_fft=n_fft, hop_length=hop_length, n_chroma=n_chroma)
    return chroma

def audio_to_spectral_contrast(audio_sample, sr=16000, n_fft=2048, hop_length=512, n_bands=6):
    stft = np.abs(librosa.stft(audio_sample, n_fft=n_fft, hop_length=hop_length))
    spectral_contrast = librosa.feature.spectral_contrast(S=stft, sr=sr, n_bands=n_bands)
    return spectral_contrast

def audio_to_tonnetz(audio_sample, sr=16000, n_bins=128):
    harmonic = librosa.effects.harmonic(audio_sample)
    tonnetz = librosa.feature.tonnetz(y=harmonic, sr=sr)
    # Reshape tonnetz to a higher dimensional representation
    tonnetz_resized = np.repeat(tonnetz, n_bins // tonnetz.shape[0], axis=0)
    return tonnetz_resized

"""save"""

target_height = 300  # Define the target height for smaller spectrograms

spectrogram_functions = {
    'stft': audio_to_spectrogram,
    'log_mel': audio_to_log_mel_spectrogram,
    'mfcc': audio_to_mfcc,
    'chroma': audio_to_chroma,
    'spectral_contrast': audio_to_spectral_contrast,
    'tonnetz': audio_to_tonnetz
}

for spectrogram_type, spectrogram_function in spectrogram_functions.items():
    spectrogram_save_dir = os.path.join(save_dir, spectrogram_type)
    os.makedirs(spectrogram_save_dir, exist_ok=True)

    for family in data_dict.keys():
        family_save_dir = os.path.join(spectrogram_save_dir, family)
        os.makedirs(family_save_dir, exist_ok=True)

        audio_samples = np.load(os.path.join(save_dir, f'{family}.npy'))
        spectrograms = []
        for audio in audio_samples:
            spec = spectrogram_function(audio)
            if spectrogram_type not in ['stft']:
                spec = resize_spectrogram(spec, target_height)
            normalized_spec = normalize_spectrogram(spec)
            spectrograms.append(normalized_spec)
        spectrograms = np.array(spectrograms)
        # np.save(os.path.join(family_save_dir, f'{family}_{spectrogram_type}.npy'), spectrograms)

print(f"Spectrograms for each instrument family have been saved to {save_dir}")

"""1. Load the spectrograms for each instrument 2. and each spectrogram type.
3. Find the largest length among the 4. spectrograms.
4. Pad the smaller spectrograms with zeros to match the largest length.
5. Combine the spectrograms for each sample.
Save the combined spectrograms in a new subfolder.
"""

import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import os
import tensorflow as tf
from PIL import Image
import numpy as np
import librosa
import cv2
import matplotlib.pyplot as plt

# Directory paths
base_dir = '/content/drive/My Drive/200-each-instrument/'
combined_save_dir = os.path.join(base_dir, 'all_combined_with_padding')
os.makedirs(combined_save_dir, exist_ok=True)
spectrogram_types = ['stft', 'log_mel', 'mfcc', 'chroma', 'spectral_contrast', 'tonnetz']
instrument_families = ['bass', 'brass', 'flute', 'guitar', 'keyboard', 'mallet', 'organ', 'reed', 'string', 'vocal']

# Function to load data
def load_data(family, spectrogram_type):
    file_path = os.path.join(base_dir, spectrogram_type, family, f'{family}_{spectrogram_type}.npy')
    return np.load(file_path)

# Combine spectrograms with padding and normalization
def concatenate_spectrograms_with_padding(spectrograms, padding_size=5):
    resized_spectrograms = []
    for spec in spectrograms:
        normalized_spec = normalize_data(spec)
        resized_spectrograms.append(normalized_spec)
        resized_spectrograms.append(np.zeros((padding_size, spec.shape[1])))
    return np.concatenate(resized_spectrograms, axis=0)

# Combine spectrograms and save
for family in instrument_families:
    all_spectrograms = []
    for spectrogram_type in spectrogram_types:
        spectrograms = load_data(family, spectrogram_type)
        all_spectrograms.append(spectrograms)

    combined_spectrograms = np.array([
        concatenate_spectrograms_with_padding([all_spectrograms[j][i] for j in range(len(spectrogram_types))])
        for i in range(all_spectrograms[0].shape[0])
    ])

    # Check for NaNs or infinite values in combined spectrograms
    check_nan_inf(combined_spectrograms)

    # Further handle any remaining NaNs or infinite values
    combined_spectrograms = np.nan_to_num(combined_spectrograms)

    # Save the combined spectrograms
    save_path = os.path.join(combined_save_dir, f'{family}_combined.npy')
    np.save(save_path, combined_spectrograms)

print(f"Combined spectrograms for each instrument have been saved to {combined_save_dir}")

# Function to plot combined spectrograms
def plot_combined_spectrograms(spectrogram, title):
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.imshow(spectrogram, aspect='auto', origin='lower', cmap='viridis')
    ax.set_title(title)
    ax.axis('off')
    plt.show()

# Load and plot a few samples from the combined spectrograms for visualization
for instrument_family in instrument_families:
    combined_spectrograms = np.load(os.path.join(combined_save_dir, f'{instrument_family}_combined.npy'))
    # for i in range(5):
     #    plot_combined_spectrograms(combined_spectrograms[i], f'Combined Spectrograms for {instrument_family} - Sample {i+1}')

"""plot"""

# Directory paths
base_dir = '/content/drive/My Drive/200-each-instrument/'
combined_save_dir = os.path.join(base_dir, 'all_combined_with_padding')
plot_save_dir = os.path.join(base_dir, 'plots')
os.makedirs(plot_save_dir, exist_ok=True)
spectrogram_types = ['stft', 'log_mel', 'mfcc', 'chroma', 'spectral_contrast', 'tonnetz']
instrument_families = ['bass', 'brass', 'flute', 'guitar', 'keyboard', 'mallet', 'organ', 'reed', 'string', 'vocal']

# Function to load data
def load_data(family, spectrogram_type=None):
    if spectrogram_type:
        file_path = os.path.join(base_dir, spectrogram_type, family, f'{family}_{spectrogram_type}.npy')
    else:
        file_path = os.path.join(base_dir, f'{family}.npy')
    return np.load(file_path)

# Function to apply a simple 2D convolution and ReLU activation
def apply_simple_conv2d_and_relu(spectrogram, scale=0.01):
    from scipy.ndimage import convolve
    kernel = np.array([[scale, scale, scale], [scale, scale, scale], [scale, scale, scale]])
    conv = convolve(spectrogram, kernel)
    relu = np.maximum(0, conv)
    return relu[..., np.newaxis]

# Function to plot combined spectrograms without any additional elements
def plot_combined_spectrograms(audio_sample, sr=16000):
    features = [audio_to_spectrogram(audio_sample, sr),
                audio_to_log_mel_spectrogram(audio_sample, sr),
                audio_to_mfcc(audio_sample, sr),
                audio_to_chroma(audio_sample, sr),
                audio_to_spectral_contrast(audio_sample, sr),
                audio_to_tonnetz(audio_sample, sr)]

    combined_feature = np.vstack(features)

    return combined_feature

# Plotting function
def plot_instrument_samples():
    for family in instrument_families:
        # Create subdirectory for storing plots
        family_plot_save_dir = os.path.join(plot_save_dir, family)
        os.makedirs(family_plot_save_dir, exist_ok=True)

        fig, axs = plt.subplots(4, 6, figsize=(30, 20))
        fig.suptitle(f'{family.capitalize()} - First Sample', fontsize=16)

        # Load and plot raw audio
        raw_audio = np.load(os.path.join(base_dir, f'{family}.npy'))[0]
        axs[3, 0].plot(raw_audio)
        axs[3, 0].set_title('Raw Audio')
        axs[3, 0].axis('off')

        # Leave two empty subplots after raw audio
        axs[3, 1].axis('off')
        axs[3, 2].axis('off')

        # Load combined spectrograms
        combined_spectrograms = np.load(os.path.join(combined_save_dir, f'{family}_combined.npy'))
        im = axs[3, 3].imshow(combined_spectrograms[0], aspect='auto', origin='lower', cmap='viridis')
        axs[3, 3].set_title('All Combined Spectrogram')
        axs[3, 3].axis('off')

        # Apply simple Conv2D and ReLU twice with smaller kernel values to combined spectrogram
        combined_conv1_spec = apply_simple_conv2d_and_relu(combined_spectrograms[0], scale=0.05)
        combined_conv2_spec = apply_simple_conv2d_and_relu(combined_conv1_spec[:, :, 0], scale=0.05)  # Apply on the first channel

        axs[3, 4].imshow(combined_conv1_spec[:, :, 0], aspect='auto', origin='lower', cmap='viridis')
        axs[3, 4].set_title('All Combined Conv2D + ReLU (1st)')
        axs[3, 4].axis('off')

        axs[3, 5].imshow(combined_conv2_spec[:, :, 0], aspect='auto', origin='lower', cmap='viridis')
        axs[3, 5].set_title('All Combined Conv2D + ReLU (2nd)')
        axs[3, 5].axis('off')

        # Load, plot, and apply Conv2D and ReLU for each spectrogram type
        for i, spectrogram_type in enumerate(spectrogram_types):
            spectrogram = load_data(family, spectrogram_type)[0]
            row = i // 2
            col = (i % 2) * 3
            if spectrogram_type in ['stft', 'log_mel']:
                librosa.display.specshow(spectrogram, sr=16000, ax=axs[row, col], x_axis='time', y_axis='log')
            elif spectrogram_type == 'mfcc':
                librosa.display.specshow(spectrogram, sr=16000, ax=axs[row, col], x_axis='time')
            elif spectrogram_type == 'chroma':
                librosa.display.specshow(spectrogram, sr=16000, ax=axs[row, col], y_axis='chroma', x_axis='time')
            elif spectrogram_type == 'spectral_contrast':
                librosa.display.specshow(spectrogram, sr=16000, ax=axs[row, col], x_axis='time')
            elif spectrogram_type == 'tonnetz':
                librosa.display.specshow(spectrogram, sr=16000, ax=axs[row, col], y_axis='tonnetz', x_axis='time')

            axs[row, col].set_title(spectrogram_type.capitalize())

            # Apply simple Conv2D and ReLU twice with smaller kernel values
            conv1_spec = apply_simple_conv2d_and_relu(spectrogram, scale=0.01)
            conv2_spec = apply_simple_conv2d_and_relu(conv1_spec[:, :, 0], scale=0.01)  # Apply on the first channel

            axs[row, col + 1].imshow(conv1_spec[:, :, 0], aspect='auto', origin='lower', cmap='viridis')
            axs[row, col + 1].set_title(f'{spectrogram_type.capitalize()} Conv2D + ReLU (1st)')
            axs[row, col + 2].imshow(conv2_spec[:, :, 0], aspect='auto', origin='lower', cmap='viridis')
            axs[row, col + 2].set_title(f'{spectrogram_type.capitalize()} Conv2D + ReLU (2nd)')

        plt.tight_layout(rect=[0, 0, 1, 0.97])

        plot_path = os.path.join(family_plot_save_dir, f'{family}_plot.png')
        plt.savefig(plot_path)
        plt.close()

# plot
plot_instrument_samples()

"""polyphony"""

import numpy as np
import os
from google.colab import drive

# Mount Google Drive
drive.mount('/content/drive')

# Directory paths
base_dir = '/content/drive/My Drive/200-each-instrument/'
combined_save_dir = os.path.join(base_dir, 'all_combined_with_padding')

# Instrument families
instrument_families = ['bass', 'brass', 'flute', 'guitar', 'keyboard', 'mallet', 'organ', 'reed', 'string', 'vocal']

# Function to load combined data
def load_combined_data(family):
    file_path = os.path.join(combined_save_dir, f'{family}_combined.npy')
    return np.load(file_path)

# Function to generate noise sample
def generate_noise_sample(shape):
    noise = np.random.randn(*shape)
    return noise

# Function to overlay spectrograms
def overlay_spectrograms(spectrograms):
    overlay = np.sum(spectrograms, axis=0) / len(spectrograms)
    return overlay

# Generate validation data
def generate_validation_data(samples_per_family, shape, num_samples_per_combination=10):
    test_samples = []
    true_labels = []

    # Generate "No Instrument" samples
    for _ in range(num_samples_per_combination):
        noise_spectrogram = generate_noise_sample(shape)
        test_samples.append(noise_spectrogram)
        true_labels.append([0] * 10)

    # Generate solo, duo, trio, etc. samples
    for num_instruments in range(1, 11):
        for _ in range(num_samples_per_combination):
            spectrograms = []
            label = [0] * 10
            selected_families = np.random.choice(list(samples_per_family.keys()), num_instruments, replace=False)
            for family_id in selected_families:
                data = samples_per_family[family_id]
                spectrogram = data[np.random.randint(0, data.shape[0])]
                spectrograms.append(spectrogram)
                label[family_id] = 1

            overlayed_spectrogram = overlay_spectrograms(spectrograms)
            test_samples.append(overlayed_spectrogram)
            true_labels.append(label)

    return np.array(test_samples), np.array(true_labels)

# Load samples per family
samples_per_family = {i: load_combined_data(family)[:50] for i, family in enumerate(instrument_families)}

# Determine the shape of the spectrograms
example_spectrogram = samples_per_family[0][0]
shape = example_spectrogram.shape

# Generate validation data
test_samples, true_labels = generate_validation_data(samples_per_family, shape)

# Save the generated data
np.save(os.path.join(base_dir, 'validation_samples.npy'), test_samples)
np.save(os.path.join(base_dir, 'validation_labels.npy'), true_labels)

print("Validation data generation completed and saved.")

"""plot and debug"""

import matplotlib.pyplot as plt

def plot_samples(test_samples, true_labels, num_samples=5):
    indices = np.random.choice(len(test_samples), num_samples, replace=False)
    for i, idx in enumerate(indices):
        plt.figure(figsize=(10, 4))
        plt.imshow(test_samples[idx], aspect='auto', origin='lower')
        plt.title(f'Label: {true_labels[idx]}')
        plt.colorbar(format='%+2.0f dB')
        plt.show()

# Example usage:
plot_samples(test_samples, true_labels, num_samples=5)
