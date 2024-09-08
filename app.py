import numpy as np
import pandas as pd
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn import svm
from sklearn.preprocessing import StandardScaler
from PIL import Image, ImageOps, ImageDraw
import logging
import PyPDF2
import re
import os
from dotenv import load_dotenv
import hashlib
from io import BytesIO
import random

# Load environment variables from .env file
load_dotenv()

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# Fetch environment variables
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SENDER_EMAIL = "16gomathimsc@gmail.com"
USER_DB_FILE = 'users.csv'

# Initialize user database
def init_user_db():
    if not os.path.exists(USER_DB_FILE):
        df = pd.DataFrame(columns=['username', 'password', 'email', 'image', 'user_id'])
        df.to_csv(USER_DB_FILE, index=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password, email, image):
    df = pd.read_csv(USER_DB_FILE) if os.path.exists(USER_DB_FILE) and os.path.getsize(USER_DB_FILE) > 0 else pd.DataFrame(columns=['username', 'password', 'email', 'image', 'user_id'])
    if username not in df['username'].values:
        hashed_password = hash_password(password)
        user_id = f"{random.randint(10000, 99999)}"  # Generate a 5-digit ID
        new_user = pd.DataFrame([[username, hashed_password, email, image, user_id]], columns=['username', 'password', 'email', 'image', 'user_id'])
        df = pd.concat([df, new_user], ignore_index=True)
        df.to_csv(USER_DB_FILE, index=False)
        return True
    return False

def authenticate_user(username, password):
    if os.path.exists(USER_DB_FILE) and os.path.getsize(USER_DB_FILE) > 0:
        df = pd.read_csv(USER_DB_FILE)
    else:
        return False
    if username in df['username'].values:
        hashed_password = hash_password(password)
        return hashed_password in df[df['username'] == username]['password'].values
    return False

# Language dictionaries
translations = {
    {
    'en': {
        'login': 'Login',
        'register': 'Register',
        'user_profile': 'User Profile',
        'username': 'Username',
        'new_username': 'New Username',
        'new_password': 'New Password',
        'email': 'Email',
        'user_id': 'User ID',
        'profile_picture': 'Profile Picture',
        'sign_out': 'Sign Out',
        'diabetes_prediction': 'Diabetes Prediction',
        'input_features': 'Input Features',
        'pregnancies': 'Pregnancies',
        'glucose': 'Glucose',
        'blood_pressure': 'Blood Pressure',
        'skin_thickness': 'Skin Thickness',
        'insulin': 'Insulin',
        'bmi': 'BMI',
        'diabetes_pedigree_function': 'Diabetes Pedigree Function',
        'age': 'Age',
        'prediction': 'Prediction',
        'risk_of_diabetes': 'You are at risk of diabetes.',
        'no_risk_of_diabetes': 'You are not at risk of diabetes. Great job maintaining your health!',
        'upload_pdf': 'Upload a PDF',
        'choose_pdf': 'Choose a PDF file',
        'extracted_pdf_data': 'Extracted PDF data',
        'pdf_prediction': 'PDF Prediction',
        'risk_of_diabetes_detected': 'Risk of diabetes detected.',
        'no_risk_of_diabetes_detected': 'No risk of diabetes detected.',
        'contact_us': 'Contact Us',
        'subject': 'Subject',
        'message': 'Message',
        'your_email': 'Your Email',
        'send': 'Send',
        'message_prepared': 'Your message has been prepared! Please check the console for the email content.',
        'fill_out_all_fields': 'Please fill out all fields.'
    },
    'ta': {
        'login': 'உள்நுழைய',
        'register': 'பதிவு',
        'user_profile': 'பயனர் சுயவிவரம்',
        'username': 'பயனர் பெயர்',
        'new_username': 'புதிய பயனர் பெயர்',
        'new_password': 'புதிய கடவுச்சொல்',
        'email': 'மின்னஞ்சல்',
        'user_id': 'பயனர் ஐடி',
        'profile_picture': 'சுயவிவரப் படம்',
        'sign_out': 'உள்நுழைவதற்கு வெளியேறு',
        'diabetes_prediction': 'மருத்துவம் பொறுத்தது',
        'input_features': 'உள்ளீட்டு அம்சங்கள்',
        'pregnancies': 'கர்ப்பக்தைகள்',
        'glucose': 'குளுக்கோஸ்',
        'blood_pressure': 'இரத்த அழுத்தம்',
        'skin_thickness': 'சகல அளவீடு',
        'insulin': 'இன்சுலின்',
        'bmi': 'உயர்திரள் அடிப்படையில்',
        'diabetes_pedigree_function': 'சர்க்கரை நோய் மரபணு செயல்பாடு',
        'age': 'வயது',
        'prediction': 'மதிப்பீடு',
        'risk_of_diabetes': 'நீங்கள் சர்க்கரை நோய்க்கு ஆபத்தாக உள்ளீர்கள்.',
        'no_risk_of_diabetes': 'நீங்கள் சர்க்கரை நோய்க்கு ஆபத்தாக இல்லீர்கள். உங்கள் உடல் நலத்தை சுட்டுங்கள்!',
        'upload_pdf': 'ஒரு PDF ஐப் பதிவேற்றவும்',
        'choose_pdf': 'ஒரு PDF கோப்பைத் தேர்வுசெய்க',
        'extracted_pdf_data': 'அல்லது PDF தரவுகள்',
        'pdf_prediction': 'PDF மதிப்பீடு',
        'risk_of_diabetes_detected': 'சர்க்கரை நோய்க்கு ஆபத்து கண்டறியப்பட்டது.',
        'no_risk_of_diabetes_detected': 'சர்க்கரை நோய்க்கு ஆபத்து இல்லை.',
        'contact_us': 'எங்களை தொடர்புகொள்',
        'subject': 'விஷயம்',
        'message': 'செய்தி',
        'your_email': 'உங்கள் மின்னஞ்சல்',
        'send': 'அனுப்பு',
        'message_prepared': 'உங்கள் செய்தி தயார் செய்யப்பட்டுள்ளது! மின்னஞ்சல் உள்ளடக்கத்தைப் பார்க்க தயவுசெய்து திரையில் சோதிக்கவும்.',
        'fill_out_all_fields': 'அனைத்து புலங்களையும் நிரப்பவும்.'
    },
    'hi': {
        'login': 'लॉगिन',
        'register': 'रजिस्टर',
        'user_profile': 'उपयोगकर्ता प्रोफाइल',
        'username': 'उपयोगकर्ता नाम',
        'new_username': 'नया उपयोगकर्ता नाम',
        'new_password': 'नया पासवर्ड',
        'email': 'ईमेल',
        'user_id': 'उपयोगकर्ता आईडी',
        'profile_picture': 'प्रोफाइल चित्र',
        'sign_out': 'साइन आउट',
        'diabetes_prediction': 'मधुमेह भविष्यवाणी',
        'input_features': 'इनपुट विशेषताएँ',
        'pregnancies': 'गर्भधारण',
        'glucose': 'ग्लूकोज',
        'blood_pressure': 'रक्तचाप',
        'skin_thickness': 'त्वचा की मोटाई',
        'insulin': 'इंसुलिन',
        'bmi': 'बीएमआई',
        'diabetes_pedigree_function': 'मधुमेह वंशावली कार्य',
        'age': 'उम्र',
        'prediction': 'भविष्यवाणी',
        'risk_of_diabetes': 'आपको मधुमेह का खतरा है।',
        'no_risk_of_diabetes': 'आपको मधुमेह का खतरा नहीं है। आपकी सेहत बनाए रखने के लिए अच्छा काम!',
        'upload_pdf': 'एक पीडीएफ अपलोड करें',
        'choose_pdf': 'एक पीडीएफ फ़ाइल चुनें',
        'extracted_pdf_data': 'निकाले गए पीडीएफ डेटा',
        'pdf_prediction': 'पीडीएफ भविष्यवाणी',
        'risk_of_diabetes_detected': 'मधुमेह का खतरा पता चला।',
        'no_risk_of_diabetes_detected': 'मधुमेह का कोई खतरा नहीं पाया गया।',
        'contact_us': 'संपर्क करें',
        'subject': 'विषय',
        'message': 'संदेश',
        'your_email': 'आपका ईमेल',
        'send': 'भेजें',
        'message_prepared': 'आपका संदेश तैयार है! कृपया ईमेल सामग्री की जांच के लिए कंसोल देखें।',
        'fill_out_all_fields': 'कृपया सभी फ़ील्ड भरें।'
    },
    'ml': {
        'login': 'ലോഗിൻ',
        'register': 'രജിസ്റ്റർ',
        'user_profile': 'ഉപയോക്തൃ പ്രൊഫൈൽ',
        'username': 'ഉപയോക്തൃനാമം',
        'new_username': 'പുതിയ ഉപയോക്തൃനാമം',
        'new_password': 'പുതിയ പാസ്വേഡ്',
        'email': 'ഇമെയിൽ',
        'user_id': 'ഉപയോക്തൃ ഐഡി',
        'profile_picture': 'പ്രൊഫൈൽ ചിത്രം',
        'sign_out': 'ലോഗ് ഔട്ട്',
        'diabetes_prediction': 'പ്രമേഹം പ്രവചനം',
        'input_features': 'ഇൻപുട്ട് ഫീച്ചറുകൾ',
        'pregnancies': 'ഗർഭാവസ്ഥകൾ',
        'glucose': 'ഗ്ലൂക്കോസ്',
        'blood_pressure': 'രക്തസമ്മർദ്ദം',
        'skin_thickness': 'ചർമ്മത്തിന്റെ കനം',
        'insulin': 'ഇൻസുലിൻ',
        'bmi': 'BMI',
        'diabetes_pedigree_function': 'പ്രമേഹം വംശാവലി പ്രവർത്തനം',
        'age': 'വയസ്സ്',
        'prediction': 'പ്രവചനം',
        'risk_of_diabetes': 'നിങ്ങൾ പ്രമേഹത്തിന് അപകടത്തിലാണു.',
        'no_risk_of_diabetes': 'നിങ്ങൾ പ്രമേഹത്തിന് അപകടത്തിലല്ല. നിങ്ങളുടെ ആരോഗ്യത്തെ സൂക്ഷിച്ച് തുടരൂ!',
        'upload_pdf': 'ഒരു PDF അപ്‌ലോഡ് ചെയ്യുക',
        'choose_pdf': 'ഒരു PDF ഫയൽ തിരഞ്ഞെടുക്കുക',
        'extracted_pdf_data': 'PDF ഡാറ്റകൾ എക്സ്ട്രാക്ട് ചെയ്തു',
        'pdf_prediction': 'PDF പ്രവചനം',
        'risk_of_diabetes_detected': 'പ്രമേഹത്തിന്റെ അപകടം കണ്ടെത്തി.',
        'no_risk_of_diabetes_detected': 'പ്രമേഹത്തിന്റെ അപകടം കണ്ടെത്തിയില്ല.',
        'contact_us': 'ഞങ്ങളെ ബന്ധപ്പെടുക',
        'subject': 'വിഷയം',
        'message': 'സന്ദേശം',
        'your_email': 'നിങ്ങളുടെ ഇമെയിൽ',
        'send': 'അയയ്ക്കുക',
        'message_prepared': 'നിങ്ങളുടെ സന്ദേശം തയ്യാറാക്കി! ദയവായി ഇമെയിൽ ഉള്ളടക്കം പരിശോധിക്കൂ.',
        'fill_out_all_fields': 'എല്ലാ ഫീൽഡുകളും പൂരിപ്പിക്കൂ.'
    },
    'te': {
        'login': 'లాగిన్',
        'register': 'నమోదు',
        'user_profile': 'వాడుకరి ప్రొఫైల్',
        'username': 'వాడుకరి పేరు',
        'new_username': 'కొత్త వాడుకరి పేరు',
        'new_password': 'కొత్త పాస్వర్డ్',
        'email': 'ఇమెయిల్',
        'user_id': 'వాడుకరి ఐడి',
        'profile_picture': 'ప్రొఫైల్ ఫోటో',
        'sign_out': 'సైన్ అవుట్',
        'diabetes_prediction': 'మధుమేహ అంచనా',
        'input_features': 'ఇన్‌పుట్ ఫీచర్లు',
        'pregnancies': 'గర్భధారణలు',
        'glucose': 'గ్లూకోజ్',
        'blood_pressure': 'రక్తపోటు',
        'skin_thickness': 'చర్మం మందం',
        'insulin': 'ఇన్సులిన్',
        'bmi': 'బిఎమ్‌ఐ',
        'diabetes_pedigree_function': 'మధుమేహ వంశవృక్షం',
        'age': 'వయస్సు',
        'prediction': 'అంచనా',
        'risk_of_diabetes': 'మీకు మధుమేహం ప్రమాదం ఉంది.',
        'no_risk_of_diabetes': 'మీకు మధుమేహం ప్రమాదం లేదు. మీ ఆరోగ్యాన్ని కాపాడుతున్నందుకు అద్భుతం!',
        'upload_pdf': 'PDF ను అప్‌లోడ్ చేయండి',
        'choose_pdf': 'PDF ఫైల్‌ను ఎంచుకోండి',
        'extracted_pdf_data': 'PDF డేటా ఉత్పత్తి చేయబడింది',
        'pdf_prediction': 'PDF అంచనా',
        'risk_of_diabetes_detected': 'మధుమేహం ప్రమాదం కనుగొనబడింది.',
        'no_risk_of_diabetes_detected': 'మధుమేహం ప్రమాదం కనుగొనబడలేదు.',
        'contact_us': 'మమ్మల్ని సంప్రదించండి',
        'subject': 'విషయం',
        'message': 'సందేశం',
        'your_email': 'మీ ఇమెయిల్',
        'send': 'పంపండి',
        'message_prepared': 'మీ సందేశం సిద్ధమైంది! ఇమెయిల్ కంటెంట్‌ను తనిఖీ చేయడానికి దయచేసి కన్సోల్‌ను పరిశీలించండి.',
        'fill_out_all_fields': 'దయచేసి అన్ని ఫీల్డ్లను పూరించండి.'
    },
    'de': {
        'login': 'Anmelden',
        'register': 'Registrieren',
        'user_profile': 'Benutzerprofil',
        'username': 'Benutzername',
        'new_username': 'Neuer Benutzername',
        'new_password': 'Neues Passwort',
        'email': 'E-Mail',
        'user_id': 'Benutzer-ID',
        'profile_picture': 'Profilbild',
        'sign_out': 'Abmelden',
        'diabetes_prediction': 'Diabetes-Vorhersage',
        'input_features': 'Eingabefunktionen',
        'pregnancies': 'Schwangerschaften',
        'glucose': 'Glukose',
        'blood_pressure': 'Blutdruck',
        'skin_thickness': 'Hautdicke',
        'insulin': 'Insulin',
        'bmi': 'BMI',
        'diabetes_pedigree_function': 'Diabetes-Stammbaumfunktion',
        'age': 'Alter',
        'prediction': 'Vorhersage',
        'risk_of_diabetes': 'Sie sind gefährdet, Diabetes zu entwickeln.',
        'no_risk_of_diabetes': 'Sie sind nicht gefährdet, Diabetes zu entwickeln. Gute Arbeit, Ihre Gesundheit zu pflegen!',
        'upload_pdf': 'Eine PDF hochladen',
        'choose_pdf': 'Eine PDF-Datei auswählen',
        'extracted_pdf_data': 'Extrahierte PDF-Daten',
        'pdf_prediction': 'PDF-Vorhersage',
        'risk_of_diabetes_detected': 'Diabetes-Risiko erkannt.',
        'no_risk_of_diabetes_detected': 'Kein Diabetes-Risiko erkannt.',
        'contact_us': 'Kontaktiere uns',
        'subject': 'Betreff',
        'message': 'Nachricht',
        'your_email': 'Ihre E-Mail',
        'send': 'Senden',
        'message_prepared': 'Ihre Nachricht wurde vorbereitet! Bitte überprüfen Sie die Konsole auf den E-Mail-Inhalt.',
        'fill_out_all_fields': 'Bitte füllen Sie alle Felder aus.'
    },
    'zh': {
        'login': '登录',
        'register': '注册',
        'user_profile': '用户资料',
        'username': '用户名',
        'new_username': '新用户名',
        'new_password': '新密码',
        'email': '电子邮件',
        'user_id': '用户ID',
        'profile_picture': '头像',
        'sign_out': '登出',
        'diabetes_prediction': '糖尿病预测',
        'input_features': '输入特征',
        'pregnancies': '怀孕',
        'glucose': '葡萄糖',
        'blood_pressure': '血压',
        'skin_thickness': '皮肤厚度',
        'insulin': '胰岛素',
        'bmi': '身体质量指数',
        'diabetes_pedigree_function': '糖尿病家系功能',
        'age': '年龄',
        'prediction': '预测',
        'risk_of_diabetes': '您有患糖尿病的风险。',
        'no_risk_of_diabetes': '您没有患糖尿病的风险。保持良好的健康状况!',
        'upload_pdf': '上传 PDF',
        'choose_pdf': '选择 PDF 文件',
        'extracted_pdf_data': '提取的 PDF 数据',
        'pdf_prediction': 'PDF 预测',
        'risk_of_diabetes_detected': '发现糖尿病风险。',
        'no_risk_of_diabetes_detected': '未检测到糖尿病风险。',
        'contact_us': '联系我们',
        'subject': '主题',
        'message': '信息',
        'your_email': '您的电子邮件',
        'send': '发送',
        'message_prepared': '您的消息已准备好! 请检查控制台中的电子邮件内容。',
        'fill_out_all_fields': '请填写所有字段。'
    },
        'es': {
        'login': 'Iniciar sesión',
        'register': 'Registrarse',
        'user_profile': 'Perfil de usuario',
        'username': 'Nombre de usuario',
        'new_username': 'Nuevo nombre de usuario',
        'new_password': 'Nueva contraseña',
        'email': 'Correo electrónico',
        'user_id': 'ID de usuario',
        'profile_picture': 'Foto de perfil',
        'sign_out': 'Cerrar sesión',
        'diabetes_prediction': 'Predicción de diabetes',
        'input_features': 'Características de entrada',
        'pregnancies': 'Embarazos',
        'glucose': 'Glucosa',
        'blood_pressure': 'Presión arterial',
        'skin_thickness': 'Espesor de la piel',
        'insulin': 'Insulina',
        'bmi': 'IMC',
        'diabetes_pedigree_function': 'Función de pedigrí de diabetes',
        'age': 'Edad',
        'prediction': 'Predicción',
        'risk_of_diabetes': 'Usted está en riesgo de diabetes.',
        'no_risk_of_diabetes': 'No está en riesgo de diabetes. ¡Buen trabajo manteniendo su salud!',
        'upload_pdf': 'Subir un PDF',
        'choose_pdf': 'Elegir un archivo PDF',
        'extracted_pdf_data': 'Datos extraídos del PDF',
        'pdf_prediction': 'Predicción del PDF',
        'risk_of_diabetes_detected': 'Riesgo de diabetes detectado.',
        'no_risk_of_diabetes_detected': 'No se detectó riesgo de diabetes.',
        'contact_us': 'Contáctanos',
        'subject': 'Asunto',
        'message': 'Mensaje',
        'your_email': 'Tu correo electrónico',
        'send': 'Enviar',
        'message_prepared': '¡Tu mensaje ha sido preparado! Por favor revisa la consola para el contenido del correo electrónico.',
        'fill_out_all_fields': 'Por favor, completa todos los campos.'
    },
        'fr': {
        'login': 'Se connecter',
        'register': 'S’inscrire',
        'user_profile': 'Profil utilisateur',
        'username': 'Nom d’utilisateur',
        'new_username': 'Nouveau nom d’utilisateur',
        'new_password': 'Nouveau mot de passe',
        'email': 'Email',
        'user_id': 'ID utilisateur',
        'profile_picture': 'Photo de profil',
        'sign_out': 'Se déconnecter',
        'diabetes_prediction': 'Prédiction du diabète',
        'input_features': 'Caractéristiques de saisie',
        'pregnancies': 'Grossesses',
        'glucose': 'Glucose',
        'blood_pressure': 'Pression artérielle',
        'skin_thickness': 'Épaisseur de la peau',
        'insulin': 'Insuline',
        'bmi': 'IMC',
        'diabetes_pedigree_function': 'Fonction de pedigree du diabète',
        'age': 'Âge',
        'prediction': 'Prédiction',
        'risk_of_diabetes': 'Vous êtes à risque de diabète.',
        'no_risk_of_diabetes': 'Vous n’êtes pas à risque de diabète. Bon travail pour maintenir votre santé !',
        'upload_pdf': 'Télécharger un PDF',
        'choose_pdf': 'Choisir un fichier PDF',
        'extracted_pdf_data': 'Données extraites du PDF',
        'pdf_prediction': 'Prédiction du PDF',
        'risk_of_diabetes_detected': 'Risque de diabète détecté.',
        'no_risk_of_diabetes_detected': 'Aucun risque de diabète détecté.',
        'contact_us': 'Nous contacter',
        'subject': 'Sujet',
        'message': 'Message',
        'your_email': 'Votre email',
        'send': 'Envoyer',
        'message_prepared': 'Votre message a été préparé ! Veuillez vérifier la console pour le contenu de l’email.',
        'fill_out_all_fields': 'Veuillez remplir tous les champs.'
    }
}

def get_translation(key):
    lang = st.session_state.get('language', 'en')
    return translations.get(lang, translations['en']).get(key, key)

def login_page():
    st.title(get_translation('login'))

    login_username = st.text_input(get_translation('username'))
    login_password = st.text_input(get_translation('password'), type="password")

    if st.button(get_translation('login')):
        if authenticate_user(login_username, login_password):
            st.session_state.logged_in = True
            st.session_state.username = login_username
            st.session_state.page = "app"  # Redirect to app page
        else:
            st.error("Invalid username or password.")

def register_page():
    st.title(get_translation('register'))

    reg_username = st.text_input(get_translation('new_username'))
    reg_password = st.text_input(get_translation('new_password'), type="password")
    reg_email = st.text_input(get_translation('email'))
    uploaded_image = st.file_uploader(get_translation('upload_image'), type=["png", "jpg", "jpeg"])

    if uploaded_image is not None:
        image_bytes = uploaded_image.read()
    else:
        image_bytes = b''

    if st.button(get_translation('register')):
        if add_user(reg_username, reg_password, reg_email, image_bytes):
            st.success(get_translation('register_success'))
            st.session_state.page = "login"  # Go to login page after registration
        else:
            st.error(get_translation('username_exists'))
    
    if st.button(get_translation('login')):
        st.session_state.page = "login"  # Allow users to go to login page

def check_login():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.write(f"{get_translation('login')} {get_translation('login')}")  # Correct port number
        st.stop()

def load_data():
    try:
        logger.debug("Loading dataset...")
        diabetes_df = pd.read_csv('diabetes.csv')
        logger.debug("Dataset loaded successfully.")
        return diabetes_df
    except FileNotFoundError as e:
        st.error(f"Error: {e}")
        logger.error(f"FileNotFoundError: {e}")
        st.stop()
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        logger.error(f"Unexpected error: {e}")
        st.stop()

def preprocess_data(df):
    try:
        logger.debug("Preprocessing data...")
        X = df.drop('Outcome', axis=1)
        y = df['Outcome']
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        logger.debug("Data preprocessing completed.")
        return X_scaled, y, scaler
    except Exception as e:
        st.error(f"An error occurred during preprocessing: {e}")
        logger.error(f"Preprocessing error: {e}")
        st.stop()

def train_model(X_train, y_train):
    try:
        logger.debug("Training model...")
        model = svm.SVC(kernel='linear')
        model.fit(X_train, y_train)
        logger.debug("Model training completed.")
        return model
    except Exception as e:
        st.error(f"An error occurred during model training: {e}")
        logger.error(f"Model training error: {e}")
        st.stop()

def get_precautionary_advice(features):
    glucose, bp, insulin, skinthickness, bmi, dpf, age = features[1:8]
    
    advice = []

    if glucose > 125:
        advice.append("• High glucose levels can be managed by reducing sugar intake, eating a balanced diet, and increasing physical activity.")
        advice.append("• Regular monitoring of blood sugar levels is important.")
        advice.append("• Consult a healthcare professional for personalized advice.")
        advice.append("• Consider joining a diabetes education program for more guidance.")
        advice.append("• Monitor glucose levels regularly to prevent complications.")

    if insulin > 30:
        advice.append("• High insulin levels can be controlled by following a healthy diet, maintaining a healthy weight, and avoiding excessive sugar intake.")
        advice.append("• Consider regular physical activity to improve insulin sensitivity.")
        advice.append("• Consult a dietitian for a personalized meal plan.")
        advice.append("• Discuss with a healthcare provider if medication adjustments are needed.")

    if dpf > 0.5:
        advice.append("• A high Diabetes Pedigree Function indicates a family history of diabetes. Maintain a healthy lifestyle and get regular check-ups.")
        advice.append("• Consider genetic counseling if there is a significant family history.")
        advice.append("• Stay informed about diabetes prevention strategies.")
        advice.append("• Monitor your health regularly for early signs of diabetes.")

    if age > 60:
        advice.append("• Older age can increase the risk of diabetes. Regular health check-ups and maintaining a healthy lifestyle are important.")
        advice.append("• Ensure regular monitoring of blood glucose levels and consult a healthcare provider for appropriate measures.")

    if glucose <= 125 and insulin <= 25 and dpf <= 0.5 and age <= 60:
        if bp > 80:
            advice.append("• High blood pressure can be managed by reducing salt intake, exercising regularly, and avoiding stress.")
            advice.append("• Monitor blood pressure frequently and take medications if prescribed.")
            advice.append("• Maintain a healthy weight and reduce alcohol consumption.")
            advice.append("• Regular check-ups with a healthcare provider are recommended.")
        
        if skinthickness > 30:
            advice.append("• Increased skin thickness can be managed by improving diet and increasing physical activity.")
            advice.append("• Monitor skin changes and consult a dermatologist if needed.")
            advice.append("• Regular exercise and a balanced diet are key.")
            advice.append("• Check for other potential underlying conditions with a healthcare provider.")
        
        if bmi > 30:
            advice.append("• A high BMI indicates obesity. Consider a balanced diet and regular exercise to maintain a healthy weight.")
            advice.append("• Aim for gradual weight loss through lifestyle changes.")
            advice.append("• Consult a healthcare provider for a weight management plan.")
            advice.append("• Avoid fad diets and focus on sustainable changes.")
            advice.append("• Incorporate both aerobic and strength training exercises.")
    
    return advice

def process_uploaded_pdf(uploaded_file):
    try:
        reader = PyPDF2.PdfFileReader(uploaded_file)
        first_page = reader.getPage(0).extract_text()
        
        values = {
            'Pregnancies': None,
            'Glucose': None,
            'Blood Pressure': None,
            'Skin Thickness': None,
            'Insulin': None,
            'BMI': None,
            'Diabetes Pedigree Function': None,
            'Age': None
        }
        
        for key in values.keys():
            match = re.search(f'{key}:\s*(\d+\.?\d*)', first_page)
            if match:
                values[key] = float(match.group(1))
        
        return list(values.values())
    except Exception as e:
        logger.error(f"PDF processing error: {e}")
        st.error("Error processing PDF. Please ensure the format is correct.")
        return None

def send_email(subject, body, to_email):
    try:
        email_content = f"Subject: {subject}\n\n{body}"
        logger.info(f"Email to be sent to {to_email}:\n{email_content}")
        st.success(get_translation('message_prepared'))
    except Exception as e:
        logger.error(f"Error preparing email: {e}")
        st.error("Failed to prepare email. Please try again.")

def main():
    init_user_db()

    if 'page' not in st.session_state:
        st.session_state.page = "register"  # Start with registration page

    if 'logged_in' in st.session_state and st.session_state.logged_in:
        st.session_state.page = "app"  # Redirect to app.py when logged in

    # Language selection
    lang = st.sidebar.selectbox(
        'Select Language',
        options=['English', 'Tamil', 'Hindi', 'French', 'Telugu', 'Malayalam', 'German', 'Chinese', 'Spanish', 'Arabic']
    )
    lang_dict = {'English': 'en', 'Tamil': 'ta', 'Hindi': 'hi', 'French': 'fr', 'Telugu' : 'te', 'Malayalam' : 'ml', 'German': 'de', 'Chinese' : 'zh', 'Spanish' : 'es', 'Arabic' : 'ar' }
    st.session_state.language = lang_dict.get(lang, 'en')
    st.session_state.language = lang_dict.get(lang, 'fr')

    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "register":
        register_page()
    elif st.session_state.page == "app":
        app()

def app():
    check_login()

    diabetes_df = load_data()
    X_scaled, y, scaler = preprocess_data(diabetes_df)
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=1)
    model = train_model(X_train, y_train)

    # Display profile image and details in the sidebar
    df = pd.read_csv(USER_DB_FILE)
    user_profile = df[df['username'] == st.session_state.username].iloc[0]

    # User ID and profile details
    user_id = user_profile['user_id']
    profile_image = user_profile['image']

    # Sidebar for user profile
    with st.sidebar.expander(get_translation('user_profile'), expanded=True):
        st.write(f"**{get_translation('username')}:** {st.session_state.username}")
        st.write(f"**{get_translation('email')}:** {user_profile['email']}")
        st.write(f"**{get_translation('user_id')}:** {user_id}")

        if profile_image and isinstance(profile_image, (bytes, bytearray)):
            image_bytes = BytesIO(profile_image)
            try:
                img = Image.open(image_bytes)
                img = img.resize((100, 100))  # Adjust size as needed
                img = ImageOps.fit(img, (100, 100), method=Image.LANCZOS)
                # Create circular mask
                mask = Image.new('L', (100, 100), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, 100, 100), fill=255)
                img.putalpha(mask)
                st.image(img, caption=get_translation('profile_picture'), use_column_width=True)
            except Exception as e:
                st.error(f"Error displaying profile image: {e}")
                logger.error(f"Profile image display error: {e}")

        if st.button(get_translation('sign_out')):
            st.session_state.logged_in = False
            st.session_state.page = "login"
            st.experimental_rerun()  # Refresh the page to redirect to login

    st.title(get_translation('diabetes_prediction'))

    st.sidebar.title(get_translation('input_features'))
    preg = st.sidebar.slider(get_translation('pregnancies'), 0, 17, 3)
    glucose = st.sidebar.slider(get_translation('glucose'), 0, 199, 117)
    bp = st.sidebar.slider(get_translation('blood_pressure'), 0, 122, 72)
    skinthickness = st.sidebar.slider(get_translation('skin_thickness'), 0, 99, 23)
    insulin = st.sidebar.slider(get_translation('insulin'), 0, 846, 30)
    bmi = st.sidebar.slider(get_translation('bmi'), 0.0, 67.1, 32.0)
    dpf = st.sidebar.slider(get_translation('diabetes_pedigree_function'), 0.078, 2.42, 0.3725, 0.001)
    age = st.sidebar.slider(get_translation('age'), 21, 81, 29)

    input_data = [preg, glucose, bp, skinthickness, insulin, bmi, dpf, age]
    logger.debug(f"Input data: {input_data}")

    reshaped_input_data = np.array(input_data).reshape(1, -1)
    scaled_input_data = scaler.transform(reshaped_input_data)
    prediction = model.predict(scaled_input_data)

    if prediction[0] == 1:
        st.write(f"**{get_translation('prediction')}:** {get_translation('risk_of_diabetes')}")
        advice = get_precautionary_advice(input_data)
        st.write(f"**{get_translation('precautionary_advice')}:**")
        for line in advice:
            st.write(line)
    else:
        st.write(f"**{get_translation('prediction')}:** {get_translation('no_risk_of_diabetes')}")

    # Move PDF upload and contact form to main area
    st.write(f"**{get_translation('upload_pdf')}**")
    uploaded_file = st.file_uploader(get_translation('choose_pdf'), type="pdf")

    if uploaded_file is not None:
        pdf_data = process_uploaded_pdf(uploaded_file)
        if pdf_data:
            st.write(f"{get_translation('extracted_pdf_data')}:", pdf_data)
            scaled_pdf_data = scaler.transform([pdf_data])
            pdf_prediction = model.predict(scaled_pdf_data)
            if pdf_prediction[0] == 1:
                st.write(f"**{get_translation('pdf_prediction')}:** {get_translation('risk_of_diabetes_detected')}")
                advice = get_precautionary_advice(pdf_data)
                st.write(f"**{get_translation('precautionary_advice_from_pdf')}:**")
                for line in advice:
                    st.write(line)
            else:
                st.write(f"**{get_translation('pdf_prediction')}:** {get_translation('no_risk_of_diabetes_detected')}")

    st.write(f"**{get_translation('contact_us')}**")
    subject = st.text_input(get_translation('subject'))
    message = st.text_area(get_translation('message'))
    email = st.text_input(get_translation('your_email'))

    if st.button(get_translation('send')):
        if subject and message and email:
            send_email(subject, message, SENDER_EMAIL)
        else:
            st.error(get_translation('fill_out_all_fields'))

def t_translation(key):
    translations = {
        'en': {
        'login': 'Login',
        'register': 'Register',
        'user_profile': 'User Profile',
        'username': 'Username',
        'new_username': 'New Username',
        'new_password': 'New Password',
        'email': 'Email',
        'user_id': 'User ID',
        'profile_picture': 'Profile Picture',
        'sign_out': 'Sign Out',
        'diabetes_prediction': 'Diabetes Prediction',
        'input_features': 'Input Features',
        'pregnancies': 'Pregnancies',
        'glucose': 'Glucose',
        'blood_pressure': 'Blood Pressure',
        'skin_thickness': 'Skin Thickness',
        'insulin': 'Insulin',
        'bmi': 'BMI',
        'diabetes_pedigree_function': 'Diabetes Pedigree Function',
        'age': 'Age',
        'prediction': 'Prediction',
        'risk_of_diabetes': 'You are at risk of diabetes.',
        'no_risk_of_diabetes': 'You are not at risk of diabetes. Great job maintaining your health!',
        'upload_pdf': 'Upload a PDF',
        'choose_pdf': 'Choose a PDF file',
        'extracted_pdf_data': 'Extracted PDF data',
        'pdf_prediction': 'PDF Prediction',
        'risk_of_diabetes_detected': 'Risk of diabetes detected.',
        'no_risk_of_diabetes_detected': 'No risk of diabetes detected.',
        'contact_us': 'Contact Us',
        'subject': 'Subject',
        'message': 'Message',
        'your_email': 'Your Email',
        'send': 'Send',
        'message_prepared': 'Your message has been prepared! Please check the console for the email content.',
        'fill_out_all_fields': 'Please fill out all fields.'
    },
    'ta': {
        'login': 'உள்நுழைய',
        'register': 'பதிவு',
        'user_profile': 'பயனர் சுயவிவரம்',
        'username': 'பயனர் பெயர்',
        'new_username': 'புதிய பயனர் பெயர்',
        'new_password': 'புதிய கடவுச்சொல்',
        'email': 'மின்னஞ்சல்',
        'user_id': 'பயனர் ஐடி',
        'profile_picture': 'சுயவிவரப் படம்',
        'sign_out': 'உள்நுழைவதற்கு வெளியேறு',
        'diabetes_prediction': 'மருத்துவம் பொறுத்தது',
        'input_features': 'உள்ளீட்டு அம்சங்கள்',
        'pregnancies': 'கர்ப்பக்தைகள்',
        'glucose': 'குளுக்கோஸ்',
        'blood_pressure': 'இரத்த அழுத்தம்',
        'skin_thickness': 'சகல அளவீடு',
        'insulin': 'இன்சுலின்',
        'bmi': 'உயர்திரள் அடிப்படையில்',
        'diabetes_pedigree_function': 'சர்க்கரை நோய் மரபணு செயல்பாடு',
        'age': 'வயது',
        'prediction': 'மதிப்பீடு',
        'risk_of_diabetes': 'நீங்கள் சர்க்கரை நோய்க்கு ஆபத்தாக உள்ளீர்கள்.',
        'no_risk_of_diabetes': 'நீங்கள் சர்க்கரை நோய்க்கு ஆபத்தாக இல்லீர்கள். உங்கள் உடல் நலத்தை சுட்டுங்கள்!',
        'upload_pdf': 'ஒரு PDF ஐப் பதிவேற்றவும்',
        'choose_pdf': 'ஒரு PDF கோப்பைத் தேர்வுசெய்க',
        'extracted_pdf_data': 'அல்லது PDF தரவுகள்',
        'pdf_prediction': 'PDF மதிப்பீடு',
        'risk_of_diabetes_detected': 'சர்க்கரை நோய்க்கு ஆபத்து கண்டறியப்பட்டது.',
        'no_risk_of_diabetes_detected': 'சர்க்கரை நோய்க்கு ஆபத்து இல்லை.',
        'contact_us': 'எங்களை தொடர்புகொள்',
        'subject': 'விஷயம்',
        'message': 'செய்தி',
        'your_email': 'உங்கள் மின்னஞ்சல்',
        'send': 'அனுப்பு',
        'message_prepared': 'உங்கள் செய்தி தயார் செய்யப்பட்டுள்ளது! மின்னஞ்சல் உள்ளடக்கத்தைப் பார்க்க தயவுசெய்து திரையில் சோதிக்கவும்.',
        'fill_out_all_fields': 'அனைத்து புலங்களையும் நிரப்பவும்.'
    },
    'hi': {
        'login': 'लॉगिन',
        'register': 'रजिस्टर',
        'user_profile': 'उपयोगकर्ता प्रोफाइल',
        'username': 'उपयोगकर्ता नाम',
        'new_username': 'नया उपयोगकर्ता नाम',
        'new_password': 'नया पासवर्ड',
        'email': 'ईमेल',
        'user_id': 'उपयोगकर्ता आईडी',
        'profile_picture': 'प्रोफाइल चित्र',
        'sign_out': 'साइन आउट',
        'diabetes_prediction': 'मधुमेह भविष्यवाणी',
        'input_features': 'इनपुट विशेषताएँ',
        'pregnancies': 'गर्भधारण',
        'glucose': 'ग्लूकोज',
        'blood_pressure': 'रक्तचाप',
        'skin_thickness': 'त्वचा की मोटाई',
        'insulin': 'इंसुलिन',
        'bmi': 'बीएमआई',
        'diabetes_pedigree_function': 'मधुमेह वंशावली कार्य',
        'age': 'उम्र',
        'prediction': 'भविष्यवाणी',
        'risk_of_diabetes': 'आपको मधुमेह का खतरा है।',
        'no_risk_of_diabetes': 'आपको मधुमेह का खतरा नहीं है। आपकी सेहत बनाए रखने के लिए अच्छा काम!',
        'upload_pdf': 'एक पीडीएफ अपलोड करें',
        'choose_pdf': 'एक पीडीएफ फ़ाइल चुनें',
        'extracted_pdf_data': 'निकाले गए पीडीएफ डेटा',
        'pdf_prediction': 'पीडीएफ भविष्यवाणी',
        'risk_of_diabetes_detected': 'मधुमेह का खतरा पता चला।',
        'no_risk_of_diabetes_detected': 'मधुमेह का कोई खतरा नहीं पाया गया।',
        'contact_us': 'संपर्क करें',
        'subject': 'विषय',
        'message': 'संदेश',
        'your_email': 'आपका ईमेल',
        'send': 'भेजें',
        'message_prepared': 'आपका संदेश तैयार है! कृपया ईमेल सामग्री की जांच के लिए कंसोल देखें।',
        'fill_out_all_fields': 'कृपया सभी फ़ील्ड भरें।'
    },
    'ml': {
        'login': 'ലോഗിൻ',
        'register': 'രജിസ്റ്റർ',
        'user_profile': 'ഉപയോക്തൃ പ്രൊഫൈൽ',
        'username': 'ഉപയോക്തൃനാമം',
        'new_username': 'പുതിയ ഉപയോക്തൃനാമം',
        'new_password': 'പുതിയ പാസ്വേഡ്',
        'email': 'ഇമെയിൽ',
        'user_id': 'ഉപയോക്തൃ ഐഡി',
        'profile_picture': 'പ്രൊഫൈൽ ചിത്രം',
        'sign_out': 'ലോഗ് ഔട്ട്',
        'diabetes_prediction': 'പ്രമേഹം പ്രവചനം',
        'input_features': 'ഇൻപുട്ട് ഫീച്ചറുകൾ',
        'pregnancies': 'ഗർഭാവസ്ഥകൾ',
        'glucose': 'ഗ്ലൂക്കോസ്',
        'blood_pressure': 'രക്തസമ്മർദ്ദം',
        'skin_thickness': 'ചർമ്മത്തിന്റെ കനം',
        'insulin': 'ഇൻസുലിൻ',
        'bmi': 'BMI',
        'diabetes_pedigree_function': 'പ്രമേഹം വംശാവലി പ്രവർത്തനം',
        'age': 'വയസ്സ്',
        'prediction': 'പ്രവചനം',
        'risk_of_diabetes': 'നിങ്ങൾ പ്രമേഹത്തിന് അപകടത്തിലാണു.',
        'no_risk_of_diabetes': 'നിങ്ങൾ പ്രമേഹത്തിന് അപകടത്തിലല്ല. നിങ്ങളുടെ ആരോഗ്യത്തെ സൂക്ഷിച്ച് തുടരൂ!',
        'upload_pdf': 'ഒരു PDF അപ്‌ലോഡ് ചെയ്യുക',
        'choose_pdf': 'ഒരു PDF ഫയൽ തിരഞ്ഞെടുക്കുക',
        'extracted_pdf_data': 'PDF ഡാറ്റകൾ എക്സ്ട്രാക്ട് ചെയ്തു',
        'pdf_prediction': 'PDF പ്രവചനം',
        'risk_of_diabetes_detected': 'പ്രമേഹത്തിന്റെ അപകടം കണ്ടെത്തി.',
        'no_risk_of_diabetes_detected': 'പ്രമേഹത്തിന്റെ അപകടം കണ്ടെത്തിയില്ല.',
        'contact_us': 'ഞങ്ങളെ ബന്ധപ്പെടുക',
        'subject': 'വിഷയം',
        'message': 'സന്ദേശം',
        'your_email': 'നിങ്ങളുടെ ഇമെയിൽ',
        'send': 'അയയ്ക്കുക',
        'message_prepared': 'നിങ്ങളുടെ സന്ദേശം തയ്യാറാക്കി! ദയവായി ഇമെയിൽ ഉള്ളടക്കം പരിശോധിക്കൂ.',
        'fill_out_all_fields': 'എല്ലാ ഫീൽഡുകളും പൂരിപ്പിക്കൂ.'
    },
    'te': {
        'login': 'లాగిన్',
        'register': 'నమోదు',
        'user_profile': 'వాడుకరి ప్రొఫైల్',
        'username': 'వాడుకరి పేరు',
        'new_username': 'కొత్త వాడుకరి పేరు',
        'new_password': 'కొత్త పాస్వర్డ్',
        'email': 'ఇమెయిల్',
        'user_id': 'వాడుకరి ఐడి',
        'profile_picture': 'ప్రొఫైల్ ఫోటో',
        'sign_out': 'సైన్ అవుట్',
        'diabetes_prediction': 'మధుమేహ అంచనా',
        'input_features': 'ఇన్‌పుట్ ఫీచర్లు',
        'pregnancies': 'గర్భధారణలు',
        'glucose': 'గ్లూకోజ్',
        'blood_pressure': 'రక్తపోటు',
        'skin_thickness': 'చర్మం మందం',
        'insulin': 'ఇన్సులిన్',
        'bmi': 'బిఎమ్‌ఐ',
        'diabetes_pedigree_function': 'మధుమేహ వంశవృక్షం',
        'age': 'వయస్సు',
        'prediction': 'అంచనా',
        'risk_of_diabetes': 'మీకు మధుమేహం ప్రమాదం ఉంది.',
        'no_risk_of_diabetes': 'మీకు మధుమేహం ప్రమాదం లేదు. మీ ఆరోగ్యాన్ని కాపాడుతున్నందుకు అద్భుతం!',
        'upload_pdf': 'PDF ను అప్‌లోడ్ చేయండి',
        'choose_pdf': 'PDF ఫైల్‌ను ఎంచుకోండి',
        'extracted_pdf_data': 'PDF డేటా ఉత్పత్తి చేయబడింది',
        'pdf_prediction': 'PDF అంచనా',
        'risk_of_diabetes_detected': 'మధుమేహం ప్రమాదం కనుగొనబడింది.',
        'no_risk_of_diabetes_detected': 'మధుమేహం ప్రమాదం కనుగొనబడలేదు.',
        'contact_us': 'మమ్మల్ని సంప్రదించండి',
        'subject': 'విషయం',
        'message': 'సందేశం',
        'your_email': 'మీ ఇమెయిల్',
        'send': 'పంపండి',
        'message_prepared': 'మీ సందేశం సిద్ధమైంది! ఇమెయిల్ కంటెంట్‌ను తనిఖీ చేయడానికి దయచేసి కన్సోల్‌ను పరిశీలించండి.',
        'fill_out_all_fields': 'దయచేసి అన్ని ఫీల్డ్లను పూరించండి.'
    },
    'de': {
        'login': 'Anmelden',
        'register': 'Registrieren',
        'user_profile': 'Benutzerprofil',
        'username': 'Benutzername',
        'new_username': 'Neuer Benutzername',
        'new_password': 'Neues Passwort',
        'email': 'E-Mail',
        'user_id': 'Benutzer-ID',
        'profile_picture': 'Profilbild',
        'sign_out': 'Abmelden',
        'diabetes_prediction': 'Diabetes-Vorhersage',
        'input_features': 'Eingabefunktionen',
        'pregnancies': 'Schwangerschaften',
        'glucose': 'Glukose',
        'blood_pressure': 'Blutdruck',
        'skin_thickness': 'Hautdicke',
        'insulin': 'Insulin',
        'bmi': 'BMI',
        'diabetes_pedigree_function': 'Diabetes-Stammbaumfunktion',
        'age': 'Alter',
        'prediction': 'Vorhersage',
        'risk_of_diabetes': 'Sie sind gefährdet, Diabetes zu entwickeln.',
        'no_risk_of_diabetes': 'Sie sind nicht gefährdet, Diabetes zu entwickeln. Gute Arbeit, Ihre Gesundheit zu pflegen!',
        'upload_pdf': 'Eine PDF hochladen',
        'choose_pdf': 'Eine PDF-Datei auswählen',
        'extracted_pdf_data': 'Extrahierte PDF-Daten',
        'pdf_prediction': 'PDF-Vorhersage',
        'risk_of_diabetes_detected': 'Diabetes-Risiko erkannt.',
        'no_risk_of_diabetes_detected': 'Kein Diabetes-Risiko erkannt.',
        'contact_us': 'Kontaktiere uns',
        'subject': 'Betreff',
        'message': 'Nachricht',
        'your_email': 'Ihre E-Mail',
        'send': 'Senden',
        'message_prepared': 'Ihre Nachricht wurde vorbereitet! Bitte überprüfen Sie die Konsole auf den E-Mail-Inhalt.',
        'fill_out_all_fields': 'Bitte füllen Sie alle Felder aus.'
    },
    'zh': {
        'login': '登录',
        'register': '注册',
        'user_profile': '用户资料',
        'username': '用户名',
        'new_username': '新用户名',
        'new_password': '新密码',
        'email': '电子邮件',
        'user_id': '用户ID',
        'profile_picture': '头像',
        'sign_out': '登出',
        'diabetes_prediction': '糖尿病预测',
        'input_features': '输入特征',
        'pregnancies': '怀孕',
        'glucose': '葡萄糖',
        'blood_pressure': '血压',
        'skin_thickness': '皮肤厚度',
        'insulin': '胰岛素',
        'bmi': '身体质量指数',
        'diabetes_pedigree_function': '糖尿病家系功能',
        'age': '年龄',
        'prediction': '预测',
        'risk_of_diabetes': '您有患糖尿病的风险。',
        'no_risk_of_diabetes': '您没有患糖尿病的风险。保持良好的健康状况!',
        'upload_pdf': '上传 PDF',
        'choose_pdf': '选择 PDF 文件',
        'extracted_pdf_data': '提取的 PDF 数据',
        'pdf_prediction': 'PDF 预测',
        'risk_of_diabetes_detected': '发现糖尿病风险。',
        'no_risk_of_diabetes_detected': '未检测到糖尿病风险。',
        'contact_us': '联系我们',
        'subject': '主题',
        'message': '信息',
        'your_email': '您的电子邮件',
        'send': '发送',
        'message_prepared': '您的消息已准备好! 请检查控制台中的电子邮件内容。',
        'fill_out_all_fields': '请填写所有字段。'
    },
        'es': {
        'login': 'Iniciar sesión',
        'register': 'Registrarse',
        'user_profile': 'Perfil de usuario',
        'username': 'Nombre de usuario',
        'new_username': 'Nuevo nombre de usuario',
        'new_password': 'Nueva contraseña',
        'email': 'Correo electrónico',
        'user_id': 'ID de usuario',
        'profile_picture': 'Foto de perfil',
        'sign_out': 'Cerrar sesión',
        'diabetes_prediction': 'Predicción de diabetes',
        'input_features': 'Características de entrada',
        'pregnancies': 'Embarazos',
        'glucose': 'Glucosa',
        'blood_pressure': 'Presión arterial',
        'skin_thickness': 'Espesor de la piel',
        'insulin': 'Insulina',
        'bmi': 'IMC',
        'diabetes_pedigree_function': 'Función de pedigrí de diabetes',
        'age': 'Edad',
        'prediction': 'Predicción',
        'risk_of_diabetes': 'Usted está en riesgo de diabetes.',
        'no_risk_of_diabetes': 'No está en riesgo de diabetes. ¡Buen trabajo manteniendo su salud!',
        'upload_pdf': 'Subir un PDF',
        'choose_pdf': 'Elegir un archivo PDF',
        'extracted_pdf_data': 'Datos extraídos del PDF',
        'pdf_prediction': 'Predicción del PDF',
        'risk_of_diabetes_detected': 'Riesgo de diabetes detectado.',
        'no_risk_of_diabetes_detected': 'No se detectó riesgo de diabetes.',
        'contact_us': 'Contáctanos',
        'subject': 'Asunto',
        'message': 'Mensaje',
        'your_email': 'Tu correo electrónico',
        'send': 'Enviar',
        'message_prepared': '¡Tu mensaje ha sido preparado! Por favor revisa la consola para el contenido del correo electrónico.',
        'fill_out_all_fields': 'Por favor, completa todos los campos.'
    },
       'fr': {
        'login': 'Se connecter',
        'register': 'S’inscrire',
        'user_profile': 'Profil utilisateur',
        'username': 'Nom d’utilisateur',
        'new_username': 'Nouveau nom d’utilisateur',
        'new_password': 'Nouveau mot de passe',
        'email': 'Email',
        'user_id': 'ID utilisateur',
        'profile_picture': 'Photo de profil',
        'sign_out': 'Se déconnecter',
        'diabetes_prediction': 'Prédiction du diabète',
        'input_features': 'Caractéristiques de saisie',
        'pregnancies': 'Grossesses',
        'glucose': 'Glucose',
        'blood_pressure': 'Pression artérielle',
        'skin_thickness': 'Épaisseur de la peau',
        'insulin': 'Insuline',
        'bmi': 'IMC',
        'diabetes_pedigree_function': 'Fonction de pedigree du diabète',
        'age': 'Âge',
        'prediction': 'Prédiction',
        'risk_of_diabetes': 'Vous êtes à risque de diabète.',
        'no_risk_of_diabetes': 'Vous n’êtes pas à risque de diabète. Bon travail pour maintenir votre santé !',
        'upload_pdf': 'Télécharger un PDF',
        'choose_pdf': 'Choisir un fichier PDF',
        'extracted_pdf_data': 'Données extraites du PDF',
        'pdf_prediction': 'Prédiction du PDF',
        'risk_of_diabetes_detected': 'Risque de diabète détecté.',
        'no_risk_of_diabetes_detected': 'Aucun risque de diabète détecté.',
        'contact_us': 'Nous contacter',
        'subject': 'Sujet',
        'message': 'Message',
        'your_email': 'Votre email',
        'send': 'Envoyer',
        'message_prepared': 'Votre message a été préparé ! Veuillez vérifier la console pour le contenu de l’email.',
        'fill_out_all_fields': 'Veuillez remplir tous les champs.'
    }
}
 
    return translations.get(st.session_state.language, translations['en']).get(key, key)

if __name__ == "__main__":
    main()
