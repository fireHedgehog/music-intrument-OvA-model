# Multi-Spectrogram Musical Instrument Classification

This repository contains the code for preparing samples, training, and testing models for musical instrument classification using various spectrogram types. The main steps include preparing the dataset, training the models, and testing the models. Below are the detailed instructions for each step.

## Prepare Samples

To prepare the samples, use the `prepare_samples.py` script. This script loads the dataset, converts audio samples to spectrograms, and saves them for training and testing.

### Usage

1. Clone the repository:
   ```bash
   git clone .... https:// .... / multi-spectrogram-experiment
   cd multi-spectrogram-experiment
    ```


### Note
This script is designed to run in Google Colab. You might need to change the file paths from Google Colab paths to your local paths.

## Train Models
To train the models using the prepared samples, use the experiment_of_6_spectrograms.py script. This script trains models using six different spectrogram types and saves the trained models.

### Usage
Run the ```experiment_of_6_spectrograms.py``` script:

### Note
Ensure that the paths in the script are updated to reflect your local paths or the paths in your Google Colab environment.

## Test Models
To test the trained models, use the ```testing_of_6_spectrograms.py``` script. This script loads the trained models and evaluates their performance on the test dataset.

### Usage
Run the ```testing_of_6_spectrograms.py``` script:

### Note
Ensure that the paths in the script are updated to reflect your local paths or the paths in your Google Colab environment.