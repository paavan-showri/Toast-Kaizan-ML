import streamlit as st
import pandas as pd

st.set_page_config(page_title='Lean AI Process Analysis Tool', layout='wide')

st.title('Lean AI Process Analysis Tool')
st.markdown(
    'Upload a Flow Process Chart file here, then open the analysis page from the left sidebar.'
)

uploaded = st.file_uploader('Upload Flow Process Chart', type=['xlsx', 'xls', 'csv'])

if uploaded is not None:
    try:
        if uploaded.name.lower().endswith('.csv'):
            df = pd.read_csv(uploaded)
        else:
            xl = pd.ExcelFile(uploaded)
            if len(xl.sheet_names) == 1:
                df = pd.read_excel(uploaded)
                st.session_state['uploaded_df'] = df
                st.session_state['uploaded_file_name'] = uploaded.name
                st.success(f"Loaded '{uploaded.name}' successfully.")
            else:
                sheet = st.selectbox('Select sheet', xl.sheet_names)
                df = pd.read_excel(uploaded, sheet_name=sheet)
                st.session_state['uploaded_df'] = df
                st.session_state['uploaded_file_name'] = uploaded.name
                st.session_state['uploaded_sheet_name'] = sheet
                st.success(f"Loaded '{uploaded.name}' ({sheet}) successfully.")

        if 'uploaded_df' not in st.session_state:
            st.session_state['uploaded_df'] = df
            st.session_state['uploaded_file_name'] = uploaded.name
            st.success(f"Loaded '{uploaded.name}' successfully.")

        st.subheader('Preview')
        st.dataframe(st.session_state['uploaded_df'].head(20), width='stretch')

    except Exception as e:
        st.error(f'Could not read the uploaded file: {e}')
else:
    st.info('Upload an Excel or CSV file to begin. Then open the page `3_5W1H_ECRSSA_Analysis` from the sidebar.')

st.divider()
st.markdown('### Session state keys used by pages')
st.code("uploaded_df\nuploaded_file_name\nuploaded_sheet_name", language='text')
