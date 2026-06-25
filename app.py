import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(layout="wide")

st.title("💻 Laptop Ranking Tool (Currys)")

# -------------------------------
# CPU benchmark lookup (simplified)
# -------------------------------
cpu_scores = {
    "i3": 6500,
    "i5": 12000,
    "i7": 18000,
    "ryzen 3": 7000,
    "ryzen 5": 14000,
    "ryzen 7": 20000
}

# -------------------------------
# Scrape Currys
# -------------------------------
@st.cache_data
def get_laptops():
    url = "https://www.currys.co.uk/computing/laptops/laptops/windows-laptops?pmin=100.0&pmax=800.0"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)

    soup = BeautifulSoup(r.text, "lxml")

    products = soup.select(".product")
    data = []

    for p in products:
        try:
            name = p.select_one(".productTitle").text.strip()
            price_raw = p.select_one(".price").text.strip()
            price = float(price_raw.replace("£", "").replace(",", ""))

            link = "https://www.currys.co.uk" + p.select_one("a")["href"]

            text = p.text.lower()

            # Extract RAM
            ram = 0
            for r_val in [4, 8, 16, 32]:
                if f"{r_val} gb ram" in text:
                    ram = r_val

            # Extract storage
            storage = 0
            for s_val in [128, 256, 512, 1024]:
                if f"{s_val} gb ssd" in text:
                    storage = s_val

            # Extract CPU
            cpu = "unknown"
            if "i3" in text:
                cpu = "i3"
            elif "i5" in text:
                cpu = "i5"
            elif "i7" in text:
                cpu = "i7"
            elif "ryzen 3" in text:
                cpu = "ryzen 3"
            elif "ryzen 5" in text:
                cpu = "ryzen 5"
            elif "ryzen 7" in text:
                cpu = "ryzen 7"

            cpu_score = cpu_scores.get(cpu, 5000)

            data.append({
                "Name": name,
                "Price": price,
                "RAM": ram,
                "Storage": storage,
                "CPU": cpu,
                "CPU Score": cpu_score,
                "Link": link
            })

        except:
            continue

    return pd.DataFrame(data)

df = get_laptops()

if df.empty:
    st.error("No laptops found — Currys structure may have changed.")
    st.stop()

# -------------------------------
# Sliders (weights)
# -------------------------------
st.sidebar.header("⚖️ Weight Your Priorities")

w_price = st.sidebar.slider("Price importance", 0.0, 1.0, 0.4)
w_ram = st.sidebar.slider("RAM importance", 0.0, 1.0, 0.2)
w_cpu = st.sidebar.slider("CPU importance", 0.0, 1.0, 0.3)
w_storage = st.sidebar.slider("Storage importance", 0.0, 1.0, 0.1)

# Normalize weights
total = w_price + w_ram + w_cpu + w_storage
w_price /= total
w_ram /= total
w_cpu /= total
w_storage /= total

# -------------------------------
# Normalisation
# -------------------------------
df["PriceScore"] = 1 - (df["Price"] - df["Price"].min()) / (df["Price"].max() - df["Price"].min())
df["RAMScore"] = df["RAM"] / df["RAM"].max()
df["CPUScore"] = df["CPU Score"] / df["CPU Score"].max()
df["StorageScore"] = df["Storage"] / df["Storage"].max()

# -------------------------------
# Final Score
# -------------------------------
df["Score"] = (
    df["PriceScore"] * w_price +
    df["RAMScore"] * w_ram +
    df["CPUScore"] * w_cpu +
    df["StorageScore"] * w_storage
)

df = df.sort_values(by="Score", ascending=False)

# -------------------------------
# Display
# -------------------------------
st.subheader("🏆 Ranked Laptops")

def make_clickable(link):
    return f'<a href="{link}" target="_blank">View</a>'

df["Link"] = df["Link"].apply(make_clickable)

st.write(
    df[["Name", "Price", "RAM", "Storage", "CPU", "Score", "Link"]]
    .to_html(escape=False, index=False),
    unsafe_allow_html=True
)
