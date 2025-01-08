import pandas as pd
import streamlit as st
import pyreadstat
import tempfile
import io

@st.cache_data()
def read_sav(dataset):
    """Carica un file SPSS e restituisce un DataFrame e i metadati."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(dataset.getvalue())
        tmp_file_path = tmp_file.name
    df, meta = pyreadstat.read_sav(tmp_file_path)
    column_labels = {col: label for col, label in zip(meta.column_names, meta.column_labels)}
    value_labels = meta.variable_value_labels
    return df, column_labels, value_labels

def rename_columns(df, metadata, selected_columns):
    """Rinomina le colonne di un DataFrame usando il dizionario dei metadati."""
    df=df[selected_columns]
    for col in selected_columns:
        if col in metadata:
            df.rename(columns={col: metadata[col]}, inplace=True)

    return df

def apply_value_labels(df, value_labels):
    """Applica i dizionari di metadati alle righe di un DataFrame."""
    for col, labels in value_labels.items():
        if col in df.columns:
            df[col] = df[col].map(labels).fillna(df[col])

def save_to_excel(df, output_path):
    """Salva il DataFrame in un file Excel."""
    df.to_excel(output_path, index=False)

# Interfaccia Streamlit
st.title("SAV to Excel Converter")

# Caricamento del file SAV
uploaded_file = st.file_uploader("Load .sav File", type=["sav"])

if uploaded_file:
    with st.spinner("Caricamento del file .sav..."):
        df, metadata, value_labels = read_sav(uploaded_file)
        st.success("File uploaded")

    st.write("File Sample:")
    st.dataframe(df.head())

    if st.checkbox("Apply rows transformation"):
        with st.spinner("Applying rows transformation"):
            apply_value_labels(df, value_labels)
            st.success("Rows successfully updated!")
        st.write("Updated rows preview:")
        st.dataframe(df.head(10))

    # Selezione delle colonne da rinominare
    columns = df.columns.tolist()
    selected_columns = st.multiselect("Select columns to rename", options=columns, default=[])

    st.write("If no colums are selected, the renaming applies to the entire database.")

    # Rinomina le colonne
    if st.button("Rename columns"):
        if not selected_columns:
            selected_columns = columns
        with st.spinner("Renaming Columns"):
            df = rename_columns(df, metadata, selected_columns)
        st.success("Colonne rinominate con successo!")
        st.dataframe(df.head())

    # Salvataggio in Excel con possibilità di scaricare
    output_file = st.text_input("Output Excel File Name", value="output.xlsx")
    # Consenti il download del file
    excel_file = io.BytesIO()
    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Survey")
    excel_file.seek(0)

    st.download_button(
        label="Export .xlsx",
        data=excel_file,
        file_name=output_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
