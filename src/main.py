import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from test_extractors import compare_extraction_methods

load_dotenv()


def get_bill_summary(bill_text, client, question=None):
    """Summarizes the bill or answers specific questions using OpenAI and tracks token usage."""
    try:
        if question:
            prompt = (f"You are a helpful assistant that provides the user ONLY and ONLY with details about their bills. "
                      f"Question: '{question}'")
        else:
            prompt = f"You are a helpful assistant that provides the user ONLY and ONLY with details about their bills. "

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": bill_text}
            ]
        )
        answer = response.choices[0].message.content
        token_usage = response.usage.total_tokens
        return answer, token_usage
    except Exception as e:
        return f"Error: {str(e)}", 0


def analyze_all_pdfs(client):
    """Analyzes all PDFs and tracks token usage."""
    data_dir = "/Users/bogdan.bolos/PycharmProjects/EONreader/src/data"
    excluded_dirs = {"casnic", "non_casnic"}
    pdf_files = [f for f in os.listdir(data_dir) if f.endswith(".pdf") and f not in excluded_dirs]

    results = []
    progress_bar = st.progress(0)
    total_files = len(pdf_files)

    for i, pdf in enumerate(pdf_files):
        pdf_path = os.path.join(data_dir, pdf)
        method_results = compare_extraction_methods(pdf_path)

        for method in method_results:
            bill_text = method.get("text", "")
            summary, tokens_used = get_bill_summary(bill_text, client) if bill_text else ("", 0)

            results.append({
                "PDF": pdf,
                "Method": method["method"],
                "Tables Found": method.get("table_count", 0),
                "Processing Time (s)": method.get("processing_time", 0),
                "Error": method.get("error", "None"),
                "Tokens Used": tokens_used  # Store token usage
            })

        progress_bar.progress((i + 1) / total_files)

    return pd.DataFrame(results)


def main():
    st.title("📄 Bill Analyzer")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.warning("Missing API key. Set OPENAI_API_KEY in your .env file.")

    client = OpenAI(api_key=api_key) if api_key else None

    mode = st.sidebar.selectbox("Choose Mode", ["Bill Chatbot", "Analyze All PDFs", "Chatbot"])

    if mode == "Bill Chatbot":
        st.subheader("Bill Chatbot")
        uploaded_file = st.file_uploader("Upload a bill PDF", type="pdf")

        if uploaded_file:
            with st.spinner("Extracting text..."):
                text_result = compare_extraction_methods(uploaded_file)[0]["text"]

            if text_result:
                st.text_area("Extracted Text", text_result[:500] + "..." if len(text_result) > 500 else text_result)

                if st.button("Summarize Bill"):
                    summary, tokens_used = get_bill_summary(text_result, client)
                    st.write(f"**Summary:** {summary}")
                    st.write(f"**Tokens Used:** {tokens_used}")

                question = st.text_input("Ask a question about the bill:")
                if question and st.button("Ask"):
                    response, tokens_used = get_bill_summary(text_result, client, question)
                    st.write(f"**Response:** {response}")
                    st.write(f"**Tokens Used:** {tokens_used}")

    elif mode == "Analyze All PDFs":
        st.subheader("📊 Analyzing All PDFs in 'data/'")
        if st.button("Run Analysis"):
            results_df = analyze_all_pdfs(client)
            st.dataframe(results_df)

    elif mode == "Chatbot":
        st.subheader("💬 Chatbot")
        if "history" not in st.session_state:
            st.session_state.history = []
        if "bill_text" not in st.session_state:
            st.session_state.bill_text = ""

        uploaded_file = st.file_uploader("Upload a bill PDF", type="pdf")
        if uploaded_file:
            with st.spinner("Extracting text..."):
                text_result = compare_extraction_methods(uploaded_file)[0]["text"]
                st.session_state.bill_text = text_result
                st.success("Bill uploaded successfully! You can now ask questions about this bill.")

        user_input = st.text_input("You:", key="user_input")
        if st.button("Send"):
            if user_input:
                st.session_state.history.append({"role": "user", "content": user_input})

                # Create system message with strong guardrails
                system_message = (
                    "You are an assistant that ONLY provides information about the uploaded E.ON energy bill. "
                    "You must REFUSE to answer ANY questions unrelated to the bill or E.ON services. "
                    "If asked about anything else, respond with: 'I can only answer questions about your E.ON bill or E.ON services. "
                    "Please ask a question related to your bill or E.ON services.'"
                )

                messages = [{"role": "system", "content": system_message}]

                # Add bill context if available
                if st.session_state.bill_text:
                    messages.append(
                        {"role": "system", "content": f"Here is the bill text: {st.session_state.bill_text}"})

                # Add conversation history
                messages.extend(st.session_state.history)

                response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=messages
                )
                bot_response = response.choices[0].message.content
                st.session_state.history.append({"role": "assistant", "content": bot_response})

        for message in st.session_state.history:
            if message["role"] == "user":
                st.write(f"**You:** {message['content']}")
            else:
                st.write(f"**Bot:** {message['content']}")

if __name__ == "__main__":
    main()