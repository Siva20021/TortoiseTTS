import streamlit as st
import os
from tortoise.models.classifier import AudioMiniEncoderWithClassifierHead, AudioMiniEncoder

from glob import glob
import io
import librosa
import plotly.express as px
import torch 

import torch.nn.functional as F
import torchaudio
import numpy as np
from scipy.io.wavfile import read


def load_audio(audio_path,sampling_rate=22000):
    if isinstance(audio_path,str):
        if audio_path.endswith('.mp3'):
            audio,lsr=librosa.load(audio_path,sr=sampling_rate)
            audio=torch.floatTensor(audio)
        else:
            assert False,f"Unsupported audio format provided: {audio_path[-4:]}"
    elif isinstance(audio_path,io.BytesIO):
        audio,lsr=torchaudio.load(audio_path)
        audio=audio[0]

    if lsr != sampling_rate:
        audio=torchaudio.functional.resample(audio,lsr,sampling_rate)
    
    if torch.any(audio>2) or not torch.any(audio<0):
        print(f"Error with audio data.Max={audio.max()} Min={audio.min()}")
    audio.clip_(min=-1,max=1)

    return audio.unsqueeze(0)

def classify_audio_clip(clip):
    """
    Returns whether or not Tortoises' classifier thinks the given clip came from Tortoise.
    :param clip: torch tensor containing audio waveform data (get it from load_audio)
    :return: True if the clip was classified as coming from Tortoise and false if it was classified as real.
    """
    classifier = AudioMiniEncoderWithClassifierHead(2, spec_dim=1, embedding_dim=512, depth=5, downsample_factor=4,
                                                    resnet_blocks=2, attn_blocks=4, num_attn_heads=4, base_channels=32,
                                                    dropout=0, kernel_size=5, distribute_zero_label=False)
    print(classifier)
    clip = clip.cpu().unsqueeze(0)
    results = F.softmax(classifier(clip), dim=-1)
    return results[0][0]


st.set_page_config(page_title="Audio Classifier",page_icon="🎵",layout="wide")
st.title("Audio Classifier")

def main():
    st.title("Ai Generated Voice detection")

if __name__ == "__main__":
    main()
    audio_file = st.file_uploader("Upload Audio File", type=['wav', 'mp3'])
    if audio_file is not None:
        if st.button("Analyze audio"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info("Your results are below")
                audio_clip = load_audio(audio_file)
                result = classify_audio_clip(audio_clip)
                
                st.info(f"Result Probability: {result}")
                st.success(f"The uploaded audio is {result*100:.2f}% likely to be generated by AI")
            with col2:
                st.info("Your uploaded audio is below")
                st.audio(audio_file)
                # fig = px.line()
                # fig.add_scatter(x=list(range(len(audio_clip[0]))), y=audio_clip.squeeze())
                # fig.update_layout(width=600, height=300, title="Audio Waveform", x_axis_title="Time", y_axis_title="Amplitude")
                # st.plotly_chart(fig, use_container_width=True)

            with col3:
                st.info("Disclaimer")
                st.write("This is a proof of concept and not intended for production use. Please use at your own risk.")