import streamlit as st
import pandas as pd
import zipfile
import io
import os

def clean_value(value):
    """Clean and standardize values for comparison"""
    if pd.isna(value):
        return None
    
    # Convert to string and remove any whitespace, special characters
    value_str = str(value).strip()
    # Remove common separators from phone numbers and other formatted strings
    value_str = ''.join(filter(str.isalnum, value_str))
    return value_str

def read_file(uploaded_file):
    if uploaded_file.name.endswith('.xlsx'):
        return pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    return None

def process_files(uploaded_files):
    if not uploaded_files:
        return {}
    
    processed_dfs = {}
    high_priority_values = set()
    
    for priority, file in enumerate(uploaded_files, 1):
        df = read_file(file)
        if df is not None and not df.empty:
            first_col = df.columns[0]
            clean_values = df[first_col].apply(clean_value)
            
            if priority == 1:
                high_priority_values.update(clean_values.dropna())
                processed_dfs[file.name] = {
                    'df': df.copy(),
                    'priority': priority
                }
            else:
                clean_value_series = clean_values.apply(
                    lambda x: x not in high_priority_values if x is not None else True
                )
                processed_dfs[file.name] = {
                    'df': df[clean_value_series].copy(),
                    'priority': priority
                }
                high_priority_values.update(clean_values.dropna())
    
    return processed_dfs

def main():
    st.title("File Priority and Duplicate Handler")
    
    uploaded_files = st.file_uploader(
        "Upload XLSX or CSV files (First upload = highest priority)", 
        type=['xlsx', 'csv'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if st.button("Process Files"):
            processed_dfs = process_files(uploaded_files)
            
            # Create zip file in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename, data in processed_dfs.items():
                    base_name = os.path.splitext(filename)[0]
                    ext = os.path.splitext(filename)[1]
                    output_filename = f"{base_name}_{data['priority']}_excluded{ext}"
                    
                    if ext == '.xlsx':
                        excel_buffer = io.BytesIO()
                        data['df'].to_excel(excel_buffer, index=False)
                        zip_file.writestr(output_filename, excel_buffer.getvalue())
                    else:
                        csv_buffer = io.StringIO()
                        data['df'].to_csv(csv_buffer, index=False)
                        zip_file.writestr(output_filename, csv_buffer.getvalue())
            
            zip_buffer.seek(0)
            st.download_button(
                label="Download Processed Files",
                data=zip_buffer.getvalue(),
                file_name="processed_files.zip",
                mime="application/zip"
            )

if __name__ == "__main__":
    main()