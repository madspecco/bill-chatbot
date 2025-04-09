import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from src.schemas import bill_extraction_schema
from src.test_extractors import extract_text_with_pdfminer

load_dotenv()


def get_bill_summary(bill_text, client, question=None):
    """Summarizes the bill or answers specific questions using OpenAI and tracks token usage."""
    try:
        prompt = (
            "You are a helpful assistant specialized in analyzing Romanian energy bills. "
            "Extract all relevant billing components such as energy consumption, price per unit, taxes (TVA), "
            "fixed charges (abonament), and any other fees. "
            "For each item, explain how the amount was calculated (e.g. '250 kWh x 0.45 RON/kWh = 112.5 RON'). "
            "Do not hallucinate values. If data is unclear or missing, say so. "
        )

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": bill_text}
        ]

        if question:
            messages.append({"role": "user", "content": f"Question: {question}"})

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages
        )
        answer = response.choices[0].message.content
        token_usage = response.usage.total_tokens
        return answer, token_usage
    except Exception as e:
        return f"Error: {str(e)}", 0


def extract_bill_items(bill_text, client):
    """Uses function calling to extract structured billing data."""
    try:
        system_message = (
            "You are an assistant that extracts billing components and calculates totals. "
            "Return the data in structured form using the provided function schema. "
            "If unit prices or quantities are not available, use empty strings."
        )

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": bill_text}
            ],
            tools=[{"type": "function", "function": bill_extraction_schema}],
            tool_choice="auto"
        )

        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            return []
        args = tool_calls[0].function.arguments
        import json
        return json.loads(args)["items"]
    except Exception as e:
        return [{"label": "Error", "quantity": "", "unit_price": "", "total": str(e)}]


def main():
    st.set_page_config(page_title="Ioana DOI – Asistent Factură", page_icon="🧾")
    st.markdown("""
        <style>
            body {
                background-color: #f9f9f9;
                font-family: 'Segoe UI', sans-serif;
            }
            .block-container {
                padding-top: 2rem;
            }
            .stButton>button {
                background-color: #004a99;
                color: white;
                border-radius: 8px;
                padding: 0.5em 1em;
                font-weight: bold;
            }
            .stTextInput>div>div>input {
                border-radius: 8px;
                padding: 0.5em;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("🧾 Ioana DOI – Asistentul tău pentru facturi E.ON")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.warning("🔑 Lipsă API key. Setează `OPENAI_API_KEY` în fișierul .env.")
    client = OpenAI(api_key=api_key) if api_key else None

    st.sidebar.title("🔧 Setări")
    mode = st.sidebar.selectbox("Mod Asistent", ["Ioana DOI (Chatbot)"])

    if mode == "Ioana DOI (Chatbot)":
        st.subheader("💬 Întrebări despre factura ta")

        if "history" not in st.session_state:
            st.session_state.history = []
        if "bill_text" not in st.session_state:
            st.session_state.bill_text = ""
        if "extraction_result" not in st.session_state:
            st.session_state.extraction_result = None

        uploaded_file = st.file_uploader("📤 Încarcă factura ta E.ON (format PDF)", type="pdf")
        if uploaded_file:
            with st.spinner("📄 Se extrage textul din factură..."):
                temp_file_path = os.path.join("/tmp", uploaded_file.name)
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                extraction_result = extract_text_with_pdfminer(temp_file_path)
                text_result = extraction_result["text"]
                st.session_state.bill_text = text_result
                st.session_state.extraction_result = extraction_result
                st.success("✅ Factură încărcată cu succes! Poți pune acum întrebări.")

        user_input = st.text_input("Tu:", key="user_input")
        if st.button("Trimite"):
            if user_input:
                st.session_state.history.append({"role": "user", "content": user_input})

                system_message = (
                    "You are an assistant named Ioana DOI who ONLY provides information about the uploaded E.ON energy bill. "
                    "You must REFUSE to answer ANY questions unrelated to the bill or E.ON services. "
                    "If asked about anything else, respond with: 'Pot să răspund doar la întrebări legate de factura E.ON sau serviciile E.ON. "
                    "Te rog întreabă ceva despre factura ta.'"
                )

                messages = [{"role": "system", "content": system_message}]

                if st.session_state.bill_text:
                    messages.append(
                        {"role": "system", "content": f"Conținutul facturii: {st.session_state.bill_text}"}
                    )

                messages.extend(st.session_state.history)

                response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=messages
                )
                bot_response = response.choices[0].message.content
                st.session_state.history.append({"role": "assistant", "content": bot_response})

        for message in st.session_state.history:
            if message["role"] == "user":
                st.markdown(f"🧍‍♂️ **Tu:** {message['content']}")
            else:
                st.markdown(f"🤖 **Ioana DOI:** {message['content']}")

if __name__ == "__main__":
    main()