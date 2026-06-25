import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(layout="wide")

st.title("💻 Laptop Ranking Tool")

# -------------------------------
# CPU benchmark lookup (basic)
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
# USER INPUT
# -------------------------------
st.subheader("🔗 Paste Currys laptop links (one per line)")
link_input = st.text_area("Laptop URLs")

# -------------------------------
# WEIGHTS
# -------------------------------
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

# -------------------------------
# SCRAPER
# -------------------------------
def scrape_laptops(links):
    headers = {"User-Agent": "Mozilla/5.0"}
    data = []

    for link in links:
        try:
            r = requests.get(link, headers=headers)
            soup = BeautifulSoup(r.text, "lxml")

            # Name
            name_tag = soup.find("h1")
            if not name_tag:
                raise Exception("Name not found")
            name = name_tag.text.strip()

            # -------- PRICE (robust search) --------
            price = None
            for tag in soup.find_all():
                if "£" in tag.text:
                    try:
                        price = float(
                            tag.text.replace("£", "")
                            .replace(",", "")
                            .strip()
                        )
                        break
                    except:
                        continue

            if price is None:
                raise Exception("Price not found")

            # -------- TEXT FOR SPEC EXTRACTION --------
            text = soup.text.lower()

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

        except Exception as e:
            st.warning(f"⚠️ Failed: {link} ({e})")

    return pd.DataFrame(data)

# -------------------------------
# RUN BUTTON
# -------------------------------
if st.button("🚀 Analyse laptops"):

    links = [l.strip() for l in link_input.split("\n") if l.strip()]

    if not links:
        st.warning("Please paste at least one link.")
    else:
        df = scrape_laptops(links)

        if df.empty:
            st.error("No laptops found.")
        else:
            # -------- NORMALISE --------
            df["PriceScore"] = 1 - (
                (df["Price"] - df["Price"].min()) /
                (df["Price"].max() - df["Price"].min() + 1e-6)
            )

            df["RAMScore"] = df["RAM"] / (df["RAM"].max() + 1e-6)
            df["CPUScore"] = df["CPU Score"] / (df["CPU Score"].max() + 1e-6)
            df["StorageScore"] = df["Storage"] / (df["Storage"].max() + 1e-6)

            # -------- FINAL SCORE --------
            df["Score"] = (
                df["PriceScore"] * w_price +
                df["RAMScore"] * w_ram +
                df["CPUScore"] * w_cpu +
                df["StorageScore"] * w_storage
            )

            df = df.sort_values(by="Score", ascending=False)

            # -------- OUTPUT --------
            st.subheader("🏆 Ranked Laptops")
            st.dataframe(df[["Name","Price","RAM","Storage","CPU","Score","Link"]])
