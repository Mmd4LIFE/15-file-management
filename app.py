import streamlit as st
import pandas as pd
import zipfile
import io
import os

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
    
    # First pass: collect all values from higher priority files
    for priority, file in enumerate(uploaded_files, 1):
        df = read_file(file)
        if df is not None and not df.empty:
            first_col = df.columns[0]
            if priority == 1:  # Highest priority file
                high_priority_values.update(df[first_col].values)
                processed_dfs[file.name] = {
                    'df': df.copy(),
                    'priority': priority
                }
            else:
                # Remove rows that exist in higher priority files
                mask = ~df[first_col].isin(high_priority_values)
                processed_dfs[file.name] = {
                    'df': df[mask].copy(),
                    'priority': priority
                }
                high_priority_values.update(df[first_col].values)
    
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