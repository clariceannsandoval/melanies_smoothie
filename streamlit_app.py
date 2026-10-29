# Import python packages
import base64
import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col

from cryptography.hazmat.primitives import serialization

# Write directly to the app
st.title(f":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write(
  """Choose the fruits you want in your custom Smoothie!
  """)

name_on_order = st.text_input('Name on Smoothie:')
st.write("The name on your Smoothie will be:", name_on_order)

# Read Snowflake settings from Streamlit Secrets
config = st.secrets["connections"]["snowflake"]

# Convert the PEM private key into Base64-encoded DER
pem_key = config["private_key"].encode("utf-8")

private_key = serialization.load_pem_private_key(
    pem_key,
    password=None,
)

private_key_der = private_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

private_key_base64 = base64.b64encode(
    private_key_der
).decode("utf-8")

# Create a Snowpark session using key-pair authentication
connection_parameters = {
    "account": config["account"],
    "user": config["user"],
    "private_key": private_key_base64,
    "role": config["role"],
    "warehouse": config["warehouse"],
    "database": config["database"],
    "schema": config["schema"],
}

@st.cache_resource
def create_snowpark_session():
    return Session.builder.configs(connection_parameters).create()

session = create_snowpark_session()

my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'))
#st.dataframe(data=my_dataframe, use_container_width=True)

ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:'
    , my_dataframe
    , max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

    #st.write(ingredients_string)

    my_insert_stmt = """ insert into smoothies.public.orders(ingredients, name_on_order)
                    values ('""" + ingredients_string + """','"""+name_on_order+ """')"""
    
    #st.write(my_insert_stmt)
    #st.stop()
    time_to_insert = st.button('Submit Order')
    
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered, '+name_on_order+'!', icon="✅")

