from semantic_router import Route
from semantic_router.encoders import HuggingFaceEncoder
from semantic_router.routers import SemanticRouter

encoder = HuggingFaceEncoder(name="sentence-transformers/all-MiniLM-L6-v2")

# ROUTE DEFINITIONS

# --- ROUTE: Human Support ---
human_support = Route(
    name='human',
    utterances=[
        "I want to talk to a human",
        "connect me to an agent",
        "speak to a real person",
        "I need customer support help",
        "this bot isn't helping, give me a person"
    ]
)

# --- ROUTE: General Assistant ---
general_help = Route(
    name='general_help',
    utterances=[
        "What can you do?",
        "How do I use this bot?",
        "Help me with my shopping",
        "Tell me about Flipkart",
        "Give me some tips"
    ]
)


# --- ROUTE: FAQ Assistant ---
faq = Route(
    name='faq',
    utterances=[
        "What is your policy on defective products?",
        "How do I return a damaged item?",
        "What is the return policy?",
        "How can I get a refund?",
        "Is there a warranty on this product?",
        "How do I track my order?",
        "Can I change my delivery address?",
        "What is the return policy of the products?",
        "Do I get discount with the HDFC credit card?",
        "How can I track my order?",
        "What payment methods are accepted?",
        "How long does it take to process a refund?",
        "Do you accept cash on delivery?",
        "What are the payment options?"
    ]
)

# --- SQL Route: Product Search and Inventory (The "Shopping Assistant") ---
sql = Route(
    name='sql',
    utterances=[
        "Pink Puma shoes in price range 5000 to 1000",
        "Show me Nike shoes under 3000.",
        "Search for cotton sarees for women.",
        "I want to buy running shoes.",
        "Are there any discounts on iPhones?",
        "Find formal shoes in size 9.",
        "I want to buy nike shoes that have 50% discount.",
        "Are there any shoes under Rs. 3000?",
        "Do you have formal shoes in size 9?",
        "Are there any Puma shoes on sale?",
        "What is the price of puma running shoes?"
    ]
)

# 3. Chitchat Route: Greetings and Small Talk
chitchat = Route(
    name='chitchat',
    utterances=[
        "Hey, how's it going?",
        "Hello!",
        "Hi, how are you today?",
        "Who are you?",
        "Good morning",
        "What's up?",
    ]
)

# INITIALIZATION

routes = [faq, sql, chitchat, human_support, general_help]

router = SemanticRouter(encoder=encoder, routes=routes, auto_sync="local")


def classify_query(query):
    guide = router(query)
    threshold = 0.4

    if guide.name is not None and guide.similarity_score > threshold:
        return guide.name

    return "fallback (General Help)"


# TESTING
if __name__ == "__main__":
    queries = [
        "What's your policy on defective products?",
        "Pink Puma shoes in price range 5000 to 1000",
        "Hey, how's it going?",
        "help me with my order"
    ]

    for q in queries:
        route = router(q)
        print(f"Query: {q} \n--> Route: {route.name if route.name else 'None'}\n")
