from dotenv import load_dotenv
import streamlit as st
import psycopg2
import os
import pandas as pd

load_dotenv()
st.set_page_config(
    layout="wide",
    initial_sidebar_state="auto",
    page_title="DA Registry Dashboard",
    page_icon=None,
)

st.title("DA Registry Dashboard")

def get_database_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

@st.cache_data
def fetch_data(query, params=None):
    connection = get_database_connection()
    cursor = connection.cursor()
    cursor.execute(query, params)
    data = cursor.fetchall()
    connection.close()
    return data

# Function to build the master query with filters
def master_query(gender_filter, education_level_filter, specialization_filter, region_filter, zone_filter, woreda_filter, kebele_filter):
    query = """
            SELECT 
                COUNT(da.id) as total_no_of_das,
                COUNT(da.id) / COUNT(DISTINCT k.id) as average_da_per_kebele,
                SUM(CASE WHEN g.name = 'Male' THEN 1 ELSE 0 END) as count_male_da,
                SUM(CASE WHEN g.name = 'Female' THEN 1 ELSE 0 END) as count_female_da,
                COUNT(DISTINCT s.id) as total_specialization,
                COUNT(DISTINCT r.id) as total_regions,
                COUNT(DISTINCT z.id) as total_zones,
                COUNT(DISTINCT w.id) as total_woredas,
                COUNT(DISTINCT k.id) as total_kebeles,
                (SELECT COUNT(da_inner.id) FROM registry_developmentagent da_inner
                JOIN registry_kebele k_inner ON da_inner.kebele_id = k_inner.id
                JOIN registry_woreda w_inner ON k_inner.woreda_id = w_inner.id
                JOIN registry_zone z_inner ON w_inner.zone_id = z_inner.id
                JOIN registry_region r_inner ON z_inner.region_id = r_inner.id) as count_da_by_region
            FROM registry_developmentagent da
            JOIN registry_kebele k ON da.kebele_id = k.id
            JOIN registry_woreda w ON k.woreda_id = w.id
            JOIN registry_zone z ON w.zone_id = z.id
            JOIN registry_region r ON z.region_id = r.id
            JOIN registry_gender g ON da.gender_id = g.id
            JOIN registry_educationlevel el ON da.education_level_id = el.id
            JOIN registry_specialization s ON da.specialization_id = s.id
            WHERE 1=1
    """
    
    if region_filter != 'none':
        query += f" AND r.name = '{region_filter}'"
    if gender_filter != 'none':
        query += f" AND g.name = '{gender_filter}'"
    if education_level_filter != 'none':
        query += f" AND el.name = '{education_level_filter}'"
    if specialization_filter != 'none':
        query += f" AND s.name = '{specialization_filter}'"
    if zone_filter != 'none':
        query += f" AND z.name = '{zone_filter}'"
    if woreda_filter != 'none':
        query += f" AND w.name = '{woreda_filter}'"
    if kebele_filter != 'none':
        query += f" AND k.name = '{kebele_filter}'"
    
    return query

# Functions to fetch filter options
def fetch_specializations():
    query = "SELECT DISTINCT name FROM registry_specialization"
    return fetch_data(query)

def fetch_education_levels():
    query = "SELECT DISTINCT name FROM registry_educationlevel"
    return fetch_data(query)

def fetch_genders():
    query = "SELECT DISTINCT name FROM registry_gender"
    return fetch_data(query)

def fetch_regions():
    query = "SELECT DISTINCT name FROM registry_region"
    return fetch_data(query)

def fetch_zones(region_name):
    query = "SELECT DISTINCT name FROM registry_zone WHERE region_id = (SELECT id FROM registry_region WHERE name = %s)"
    return fetch_data(query, [region_name])

def fetch_woredas(zone_name):
    query = "SELECT DISTINCT name FROM registry_woreda WHERE zone_id = (SELECT id FROM registry_zone WHERE name = %s)"
    return fetch_data(query, [zone_name])

def fetch_kebeles(woreda_name):
    query = "SELECT DISTINCT name FROM registry_kebele WHERE woreda_id = (SELECT id FROM registry_woreda WHERE name = %s)"
    return fetch_data(query, [woreda_name])

# Helper function to convert fetched data to list of strings
def populate_dropdown(data):
    return ["none"] + [item[0] for item in data]

def main():
    with open("style.css", "r") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    
    st.subheader("Total Stats")
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    st.subheader("Filter by")
    col21, col22, col23, col24, col25, col26, col27 = st.columns([1, 1, 1, 1, 1, 1, 1])
    
    # Fetch initial filter options
    specializations = populate_dropdown(fetch_specializations())
    education_levels = populate_dropdown(fetch_education_levels())
    genders = populate_dropdown(fetch_genders())
    regions = populate_dropdown(fetch_regions())
    
    # Input filters
    region_filter = col21.selectbox("Region", regions)
    
    if region_filter != 'none':
        zones = populate_dropdown(fetch_zones(region_filter))
    else:
        zones = ["none"]
    zone_filter = col22.selectbox("Zone", zones)

    if zone_filter != 'none':
        woredas = populate_dropdown(fetch_woredas(zone_filter))
    else:
        woredas = ["none"]
    woreda_filter = col23.selectbox("Woreda", woredas)

    if woreda_filter != 'none':
        kebeles = populate_dropdown(fetch_kebeles(woreda_filter))
    else:
        kebeles = ["none"]
    kebele_filter = col24.selectbox("Kebele", kebeles)

    gender_filter = col25.selectbox("Gender", genders)
    education_level_filter = col26.selectbox("Education Level", education_levels)
    specialization_filter = col27.selectbox("Specialization", specializations)
    
    master_data = fetch_data(master_query(gender_filter, education_level_filter, specialization_filter, region_filter, zone_filter, woreda_filter, kebele_filter))
    result = master_data[0]
    # Assign the values to descriptive variable names
    total_no_of_das = result[0]
    average_da_per_kebele = result[1]
    count_male_da = result[2]
    count_female_da = result[3]
    total_specialization = result[4]
    total_regions = result[5]
    total_zones = result[6]
    total_woredas = result[7]
    total_kebeles = result[8]
    count_da_by_region = result[9]

    # Print the values or use them as needed
    print("Total number of Development Agents:", total_no_of_das)
    print("Average number of Development Agents per Kebele:", average_da_per_kebele)
    print("Count of Male Development Agents:", count_male_da)
    print("Count of Female Development Agents:", count_female_da)
    print("Total number of Specializations:", total_specialization)
    print("Total number of Regions:", total_regions)
    print("Total number of Zones:", total_zones)
    print("Total number of Woredas:", total_woredas)
    print("Total number of Kebeles:", total_kebeles)
    print("Count of Development Agents by Region:", count_da_by_region)
    with col1:
        st.markdown(f'<div class="card"><div class="title"></div><div class="sub-title"><span class="bullet_green">&#8226;</span> {"efebfewbfjwenbfjkewnfjkewbfjdbejfwebdbewj"}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="card"><div class="title"></div><div class="sub-title"><span class="bullet_green">&#8226;</span> {"efebfewbfjwenbfjkewnfjkewbfjdbejfwebdbewj"}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="card"><div class="title"></div><div class="sub-title"><span class="bullet_green">&#8226;</span> {"efebfewbfjwenbfjkewnfjkewbfjdbejfwebdbewj"}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="card"><div class="title"></div><div class="sub-title"><span class="bullet_green">&#8226;</span> {"efebfewbfjwenbfjkewnfjkewbfjdbejfwebdbewj"}</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="card"><div class="title"></div><div class="sub-title"><span class="bullet_green">&#8226;</span> {"efebfewbfjwenbfjkewnfjkewbfjdbejfwebdbewj"}</div></div>', unsafe_allow_html=True)
    with col6:
        st.markdown(f'<div class="card"><div class="title"></div><div class="sub-title"><span class="bullet_green">&#8226;</span> {"efebfewbfjwenbfjkewnfjkewbfjdbejfwebdbewj"}</div></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
