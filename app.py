import streamlit as st
import pandas as pd
import re
from datetime import datetime
import os
from urllib.parse import quote_plus

FILE_NAME = "RBTXPartsList.xlsx"


def initialize_file():
    if not os.path.exists(FILE_NAME):
        df = pd.DataFrame(columns=[
            "RBTX PN",
            "Manufacturer",
            "Manufacturer PN",
            "Description",
            "Cost",
            "Date Added"
        ])
        df.to_excel(FILE_NAME, index=False)


def load_data():
    return pd.read_excel(FILE_NAME)


def save_data(df):
    df.to_excel(FILE_NAME, index=False)


def get_prefix(manufacturer):
    manufacturer = manufacturer.lower().strip()

    if manufacturer in ["mcmaster", "mcmaster-carr", "automationdirect", "automation direct"]:
        return "RBTX-MAT-"
    elif manufacturer == "smc":
        return "RBTX-SMC-"
    elif manufacturer == "eaton":
        return "RBTX-ETN-"
    elif manufacturer == "zimmer":
        return "RBTX-ZIM-"
    else:
        return None


def generate_part_number(df, prefix):
    matching = df[df["RBTX PN"].astype(str).str.startswith(prefix, na=False)]

    if matching.empty:
        return f"{prefix}0001"

    max_num = 0

    for part in matching["RBTX PN"]:
        match = re.search(r"(\d+)$", str(part))
        if match:
            max_num = max(max_num, int(match.group(1)))

    return f"{prefix}{max_num + 1:04d}"


def build_description(manufacturer, manufacturer_pn, website_description):
    if website_description.strip() == "":
        return f"{manufacturer} - {manufacturer_pn}"
    return f"{manufacturer} - {manufacturer_pn}; {website_description}"


def part_exists(df, manufacturer_pn):
    return df[df["Manufacturer PN"].astype(str).str.lower() == manufacturer_pn.lower().strip()]


initialize_file()

st.title("ERP Part Intake Tool")

menu = st.selectbox("Choose an action", ["Search Existing Part", "Create New Part"])

df = load_data()

if menu == "Search Existing Part":
    st.subheader("Search Existing Part")

    search_term = st.text_input("Enter RBTX PN, Manufacturer, Manufacturer PN, or Description")

    if st.button("Search"):
        results = df[
            df["RBTX PN"].astype(str).str.contains(search_term, case=False, na=False) |
            df["Manufacturer"].astype(str).str.contains(search_term, case=False, na=False) |
            df["Manufacturer PN"].astype(str).str.contains(search_term, case=False, na=False) |
            df["Description"].astype(str).str.contains(search_term, case=False, na=False)
        ]

        if results.empty:
            st.warning("No matching part found.")
        else:
            st.success("Matching part(s) found:")
            st.dataframe(results)

elif menu == "Create New Part":
    st.subheader("Create New Part")

    manufacturer = st.selectbox(
        "Manufacturer",
        ["McMaster-Carr", "AutomationDirect", "SMC", "Eaton", "Zimmer"]
    )

    manufacturer_pn = st.text_input("Manufacturer PN")

    if manufacturer_pn:
        pn_query = f"{manufacturer} {manufacturer_pn} product specifications description"
        pn_url = f"https://www.google.com/search?q={quote_plus(pn_query)}"
        st.markdown(f"[Search web by Manufacturer PN]({pn_url})")

    description_search = st.text_input("Search by Description (Optional)")

    if description_search:
        desc_query = f"{manufacturer} {description_search} product catalog specifications"
        desc_url = f"https://www.google.com/search?q={quote_plus(desc_query)}"
        st.markdown(f"[Search web by Description]({desc_url})")

    website_description = st.text_input("Website Description (Optional)")
    cost = st.text_input("Cost (Optional)")

    if st.button("Generate and Save Part"):

        if not manufacturer_pn:
            st.error("Please enter a Manufacturer PN.")

        else:
            existing = part_exists(df, manufacturer_pn)

            if not existing.empty:
                st.warning("This Manufacturer PN already exists.")
                st.dataframe(existing)

            else:
                prefix = get_prefix(manufacturer)

                if prefix is None:
                    st.error("Invalid manufacturer selected.")

                else:
                    new_part_number = generate_part_number(df, prefix)

                    description = build_description(
                        manufacturer,
                        manufacturer_pn,
                        website_description
                    )

                    new_row = pd.DataFrame([{
                        "RBTX PN": new_part_number,
                        "Manufacturer": manufacturer,
                        "Manufacturer PN": manufacturer_pn,
                        "Description": description,
                        "Cost": cost,
                        "Date Added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }])

                    df = pd.concat([df, new_row], ignore_index=True)

                    save_data(df)

                    st.success(f"New part created: {new_part_number}")

                    st.dataframe(new_row)