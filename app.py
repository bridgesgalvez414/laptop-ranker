import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(layout="wide")

st.title("💻 Laptop Ranking Tool")

cpu_scores = {
    "i3": 6500,
    "i5": 12000,
    "i7": 18000,
    "ryzen 3": 7000,
    "ryzen 5": 14000,
    "ryzen 7": 20000
}

st.subheader("🔗 Paste Currys laptop links (one per line)")
link_input = st.text_area("Laptop URLs")

st.sidebar.header("⚖️ Weight Importance")

w_price = st.sidebar.slider("Price", 0.0, 1.0, 0.4)
w_ram = st.sidebar.slider("RAM", 0.0, 1.0, 0.2)
w_cpu = st.sidebar.slider("CPU", 0.0, 1.0, 0.3)
w_storage = st.sidebar.slider("Storage", 0.0, 1.0, 0.1)

total = w_price + w_ram + w_cpu + w_storage
w_price /= total
w_ram /= total
w_cpu /= total
w_storage /= total

def scrape_laptops(links):
    headers = {"User-Agent": "Mozilla/5.0"}
    data = []

    for link in links:
        try:
            r = requests.get(link, headers=headers)
            soup = BeautifulSoup(r.text, "lxml")

            name = soup.find("h1").text.strip()

            price_tag = soup.find("strong")
            price = float(price_tag.text.replace("£", "").replace(",", ""))

            text = soup.text.lower()

            ram = next((r for r in [4, 8, 16, 32] if f"{r} gb ram" in text), 0)
            storage = next((s for s in [128, 256, 512, 1024] if f"{s} gb ssd" in text), 0)

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
            st.warning(f"⚠️ Failed: {link}")

    return pd.DataFrame(data)

if st.button("🚀 Analyse laptops"):

    links = [l.strip() for l in link_input.split("\n") if l.strip()]

    if not links:
        st.warning("Please paste at least one link.")
    else:
        df = scrape_laptops(links)

        if df.empty:
            st.error("No laptops found.")
        else:
            df["PriceScore"] = 1 - (
                (df["Price"] - df["Price"].min()) /
                (df["Price"].max() - df["Price"].min() + 1e-6)
            )

            df["RAMScore"] = df["RAM"] / (df["RAM"].max() + 1e-6)
            df["CPUScore"] = df["CPU Score"] / (df["CPU Score"].max() + 1e-6)
            df["StorageScore"] = df["Storage"] / (df["Storage"].max() + 1e-6)

            df["Score"] = (
                df["PriceScore"] * w_price +
                df["RAMScore"] * w_ram +
                df["CPUScore"] * w_cpu +
                df["StorageScore"] * w_storage
            )

            df = df.sort_values(by="Score", ascending=False)

            st.subheader("🏆 Ranked Laptops")
            st.dataframe(df[["Name","Price","RAM","Storage","CPU","Score","Link"]])
