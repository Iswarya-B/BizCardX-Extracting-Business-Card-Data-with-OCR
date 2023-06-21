import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import psycopg2

# Connecting with database
conn = psycopg2.connect(host="localhost", user="postgres", password="Smile!098", port=5432, database="bizcard")
cur = conn.cursor()

st.set_page_config(layout="wide")
st.title("BizCardX: Extracting Business Card Data with OCR")

# Customizing the page
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

selected = option_menu(
    menu_title=None,
    options=["Home", "Extract text from image", "Contact"],
    icons=["house", "image", "envelope"],
    default_index=0,
    orientation="horizontal"
)


def extracted_text(picture):
    ext_dic = {'Name': [], 'Designation': [], 'Company name': [], 'Contact': [], 'Email': [], 'Website': [],
               'Address': [], 'Pincode': []}

    ext_dic['Name'].append(result[0])
    ext_dic['Designation'].append(result[1])

    for m in range(2, len(result)):
        if result[m].startswith('+') or (result[m].replace('-', '').isdigit() and '-' in result[m]):
            ext_dic['Contact'].append(result[m])

        elif '@' in result[m] and '.com' in result[m]:
            small = result[m].lower()
            ext_dic['Email'].append(small)

        elif 'www' in result[m] or 'WWW' in result[m] or 'wwW' in result[m]:
            small = result[m].lower()
            ext_dic['Website'].append(small)

        elif 'TamilNadu' in result[m] or 'Tamil Nadu' in result[m] or result[m].isdigit():
            ext_dic['Pincode'].append(result[m])

        elif re.match(r'^[A-Za-z]', result[m]):
            ext_dic['Company name'].append(result[m])

        else:
            removed_colon = re.sub(r'[,;]', '', result[m])
            ext_dic['Address'].append(removed_colon)

    for key, value in ext_dic.items():
        if len(value) > 0:
            concatenated_string = ' '.join(value)
            ext_dic[key] = [concatenated_string]
        else:
            value = 'NA'
            ext_dic[key] = [value]

    return ext_dic


if selected == "Home":
    st.header("Welcome to our Image-to-Text Conversion Tool!")
    st.markdown("")
    st.write("Unlock the power of seamless image-to-text conversion where you can effortlessly transform visual "
             "content into editable text. Experience the convenience and efficiency of our state-of-the-art online "
             "tool. Whether you need to extract information or convert visual content into an editable format, "
             "our tool simplifies the entire process. Trust in our tool to streamline your workflow and achieve "
             "accurate results. Start converting your images to text seamlessly today.")

elif selected == "Extract text from image":
    image = st.file_uploader(label="Upload the image", type=['png', 'jpg', 'jpeg'], label_visibility="hidden")


    @st.cache_data
    def load_image():
        reader = easyocr.Reader(['en'], model_storage_directory=".")
        return reader


    reader_1 = load_image()
    if image is not None:
        input_image = Image.open(image)
        # Setting Image size
        st.image(input_image, width=350, caption='Uploaded Image')
        st.markdown(
            f'<style>.css-1aumxhk img {{ max-width: 300px; }}</style>',
            unsafe_allow_html=True
        )

        result = reader_1.readtext(np.array(input_image), detail=0)

        # creating dataframe
        ext_text = extracted_text(result)
        df = pd.DataFrame(ext_text)
        st.dataframe(df)

        # Database
        col1, col2, col3 = st.columns([1, 6, 1])
        with col2:
            selected = option_menu(
                menu_title=None,
                options=["Modify", "Delete"],
                default_index=0,
                orientation="horizontal"
            )

            ext_text = extracted_text(result)
            df = pd.DataFrame(ext_text)

        if selected == "Modify":
            col_1, col_2 = st.columns([4, 4])
            with col_1:
                modified_n = st.text_input('Name', ext_text["Name"][0])
                modified_d = st.text_input('Designation', ext_text["Designation"][0])
                modified_c = st.text_input('Company name', ext_text["Company name"][0])
                modified_con = st.text_input('Mobile', ext_text["Contact"][0])
                df["Name"], df["Designation"], df["Company name"], df["Contact"] = modified_n, modified_d, modified_c, modified_con
            with col_2:
                modified_m = st.text_input('Email', ext_text["Email"][0])
                modified_w = st.text_input('Website', ext_text["Website"][0])
                modified_a = st.text_input('Address', ext_text["Address"][0])
                modified_p = st.text_input('Pincode', ext_text["Pincode"][0])
                df["Email"], df["Website"], df["Address"], df["Pincode"] = modified_m, modified_w, modified_a, modified_p

            col3, col4 = st.columns([4, 4])
            with col3:
                Preview = st.button("Preview modified text")
            with col4:
                Upload = st.button("Upload")
            if Preview:
                st.dataframe(df)
            else:
                pass

            if Upload:
                with st.spinner("In progress"):
                    cur.execute("CREATE TABLE IF NOT EXISTS BUSINESS_CARD(NAME VARCHAR(50), DESIGNATION VARCHAR(100), "
                                "COMPANY_NAME VARCHAR(100), CONTACT VARCHAR(35), EMAIL VARCHAR(100), WEBSITE VARCHAR("
                                "100), ADDRESS TEXT, PINCODE VARCHAR(10))")
                    conn.commit()
                    A = "INSERT INTO BUSINESS_CARD(NAME, DESIGNATION, COMPANY_NAME, CONTACT, EMAIL, WEBSITE, ADDRESS, " \
                        "PINCODE) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    for index, i in df.iterrows():
                        result_table = (i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7])
                        cur.execute(A, result_table)
                        conn.commit()
                st.balloons()

        else:
            col1, col2 = st.columns([4, 4])
            with col1:
                cur.execute("SELECT NAME FROM BUSINESS_CARD")
                Y = cur.fetchall()
                names = ["Select"]
                for i in Y:
                    names.append(i[0])
                name_selected = st.selectbox("Select the name to delete", options=names)
                # st.write(name_selected)
            with col2:
                cur.execute(f"SELECT DESIGNATION FROM BUSINESS_CARD WHERE NAME = '{name_selected}'")
                Z = cur.fetchall()
                designation = ["Select"]
                for j in Z:
                    designation.append(j[0])
                designation_selected = st.selectbox("Select the designation of the chosen name", options=designation)

            st.markdown(" ")

            col_a, col_b, col_c = st.columns([5, 3, 3])
            with col_b:
                remove = st.button("Clik here to delete")
            if name_selected and designation_selected and remove:
                cur.execute(f"DELETE FROM BUSINESS_CARD WHERE NAME = '{name_selected}' AND DESIGNATION = '{designation_selected}'")
                conn.commit()
                st.balloons()

    else:
        st.write("Upload an image")

else:
    st.markdown(" ")
    st.write("Actively seeking opportunities and connections in the professional sphere. Let's connect on "
             "LinkedIn to explore potential collaborations and share valuable insights. You can also explore my "
             "diverse range of projects on GitHub to get a deeper understanding of my expertise and contributions. "
             "For any inquiries or further discussions, feel free to reach out to me via email. I am eagerly "
             "looking forward to engaging in meaningful discussions and exploring new prospects together.")

    col1, col2, col3 = st.columns([3, 3, 2])
    with col1:
        st.markdown(" ")
        st.subheader("LinkedIn")
        st.markdown("www.linkedin.com/in/iswaryabalu")
    with col2:
        st.markdown(" ")
        st.subheader("GitHub")
        st.markdown("https://github.com/Iswarya-B")
    with col3:
        st.markdown(" ")
        st.subheader("Email")
        st.markdown("iswaryabalu@yahoo.com")
