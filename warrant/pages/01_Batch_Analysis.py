import streamlit as st
from batch_processing import batch_page

# Set page configuration
st.set_page_config(
    page_title="Batch Warrant Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check for Streamlit's query parameters
query_params = st.query_params
    
# If this is the initial load with the 'Page not found' error
if '_' in query_params:
    # Create a loading spinner that automatically disappears
    with st.spinner("Loading Batch Warrant Analysis..."):
        # Sleep for a very short time
        time.sleep(0.1)
        
    # This prevents the "Page not found" message from appearing
    st.query_params.clear()

# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 500;
        color: #0D47A1;
    }
    .info-text {
        font-size: 1rem;
        color: #37474F;
    }
    .highlight {
        background-color: #E3F2FD;
        padding: 0.5rem;
        border-radius: 0.5rem;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        font-weight: 500;
        border-radius: 0.5rem;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #0D47A1;
    }
</style>
""", unsafe_allow_html=True)

# Run the batch processing page
batch_page()

# Add footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666;">
    <p>Batch analysis tool for analyzing multiple warrants simultaneously.</p>
    </div>
    """, 
    unsafe_allow_html=True
)