import streamlit as st
from router import classify_query
from faq import ingest_faq_data, faq_chain
from sql import sql_chain
from pathlib import Path

# Initialize FAQ data from your local CSV
faqs_path = Path(__file__).parent / "resources/faq_data.csv"
ingest_faq_data(faqs_path)


# --- HELPER: Display Product Cards ---
def display_product_cards(products):
    """
    Displays product search results in a professional 2-column grid.
    Expects a list of dictionaries with keys: product_link, brand, title, price, avg_rating.
    """
    if not products or not isinstance(products, list):
        # Fallback if no products are found or if an error message is passed
        st.write(products)
        return

    # Create rows with 2 products per row
    for i in range(0, len(products), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(products):
                item = products[i + j]
                with cols[j]:
                    # Using a container with a border for a card-like look
                    with st.container(border=True):
                        # Use a placeholder image if the link is missing
                        img_url = item.get('product_link', 'https://via.placeholder.com/150')
                        st.image(img_url, use_container_width=True)

                        st.subheader(item.get('brand', 'Product'))
                        st.write(f"**{item.get('title', '')}**")
                        st.write(f"Price: ₹{item.get('price', 'N/A')}")
                        st.write(f"Rating: ⭐ {item.get('avg_rating', '0')}")

                        # Direct link to the product on the store
                        st.link_button("View on Flipkart", item.get('product_link', '#'))


# --- CORE LOGIC: Process User Query ---
def ask(query):
    """
    Routes the query and returns the route name and the response data.
    """
    route = classify_query(query)

    # Display a spinner to indicate the bot is processing
    with st.spinner(f"Thinking..."):
        if route == 'faq':
            response = faq_chain(query)
        elif route == 'sql':
            # Note: sql_chain returns a string for the chat and
            # its results will be caught by the UI logic below
            response = sql_chain(query)
        elif route == 'chitchat':
            response = "Hello! I'm your Flipkart assistant. How can I help you shop today?"
        elif route == 'human':
            response = "I'm connecting you to a live agent. Please stay online."
        else:
            # Fallback for general help or unrecognized intents
            response = "I can help you find products or answer questions about returns and payments. What can I do for you?"

    return route, response


# --- STREAMLIT UI SETUP ---
st.set_page_config(page_title="Flipkart Shopping Bot", page_icon="🛍️")
st.title('🛍️ Flipkart Shopping Assistant')

# Initialize chat history session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display entire chat history on refresh
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Check if the content is a list of products to display as cards
        if isinstance(message["content"], list):
            display_product_cards(message["content"])
        else:
            st.markdown(message["content"])

# User Chat Input
if query := st.chat_input("How can I help you today?"):
    # 1. Display and save user message
    st.chat_message("user").markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})

    # 2. Get response from the bot
    with st.chat_message("assistant"):
        route, response = ask(query)

        # 3. Handle specific SQL display logic
        # If the SQL route is active, we check if the response contains data
        # Note: If your sql_chain returns a string answer, use st.markdown.
        # If you modify sql_chain to return the raw list, use display_product_cards.
        if route == 'sql' and isinstance(response, list):
            display_product_cards(response)
        else:
            st.markdown(response)

    # 4. Save assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})