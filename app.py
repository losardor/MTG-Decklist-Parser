import streamlit as st
import pandas as pd
from list2table import *

st.title("MTG Decklist to Table Converter")
uploaded_file = st.file_uploader("Upload your decklist (.txt)", type="txt")

if uploaded_file is not None:
    decklist = uploaded_file.read().decode("utf-8").splitlines()
    df = process_full_deck(decklist)  # Call your function
    st.dataframe(df)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "decklist_analysis.csv", "text/csv")
