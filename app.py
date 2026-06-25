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
@st.cache_data

def get_laptops():
    base_url = "https://www.currys.co.uk"
    url = base_url + "/computing/laptops/laptops/windows-laptops?pmin=100.0&pmax=800.0"

    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "lxml")

    # Step 1: find product links
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/products/" in href and href.endswith(".html"):
            full_link = base_url + href
            if full_link not in links:
                links.append(full_link)

    data = []

    # Step 2: scrape each product page
    for link in links[:20]:  # limit to avoid slow loading
        try:
            page = requests.get(link, headers=headers)
            psoup = BeautifulSoup(page.text, "lxml")

            name = psoup.find("h1").text.strip()

            # Price
            price_tag = psoup.find("strong")
            price = float(price_tag.text.replace("£", "").replace(",", ""))

            text = psoup.text.lower()

            # RAM
            ram = next((r for r in [4, 8, 16, 32] if f"{r} gb ram" in text), 0)

            # Storage
            storage = next((s for s in [128, 256, 512, 1024] if f"{s} gb ssd" in text), 0)

            # CPU
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
