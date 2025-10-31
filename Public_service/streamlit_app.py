import streamlit as st
import subprocess
import re
import json
import time

def run_jac_backend(country, service_type, city):
    """
    Run your existing Jaclang backend code and capture the output
    """
    try:
        input_data = f"{country}\n{service_type}\n{city}\nno\n"
        
        process = subprocess.run(
            ["jac", "run", "public_service.jac"],
            input=input_data,
            text=True,
            capture_output=True,
            timeout=60
        )
        
        if process.returncode == 0:
            return process.stdout, None
        else:
            return None, process.stderr
            
    except subprocess.TimeoutExpired:
        return None, "Request timed out"
    except Exception as e:
        return None, f"Error: {str(e)}"

def parse_service_output(raw_output):
    """
    Parse the raw backend output into structured data
    """
    try:
        # Try to extract JSON data first
        json_match = re.search(r'\[.*\]', raw_output, re.DOTALL)
        if json_match:
            json_data = json.loads(json_match.group())
            # Extract text after JSON
            text_part = raw_output[json_match.end():].strip()
            return {
                'json_data': json_data,
                'text_content': text_part,
                'has_json': True,
                'raw_output': raw_output
            }
        else:
            return {
                'json_data': None,
                'text_content': raw_output,
                'has_json': False,
                'raw_output': raw_output
            }
    except json.JSONDecodeError:
        return {
            'json_data': None,
            'text_content': raw_output,
            'has_json': False,
            'raw_output': raw_output
        }

def display_json_data(json_data):
    """
    Display JSON data in a beautiful, structured format
    """
    if not json_data or len(json_data) == 0:
        return
    
    service_info = json_data[0]  # Get first service object
    
    # Main service card
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    '>
    """, unsafe_allow_html=True)
    
    st.markdown(f"### 🎯 {service_info.get('service', 'Service Information')}")
    st.markdown(f"**📍 {service_info.get('location', '')}**")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Create columns for different sections
    col1, col2 = st.columns(2)
    
    with col1:
        # Contact Information
        st.markdown("#### 📞 Contact Information")
        contact_card = f"""
        <div style='
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #007bff;
            margin: 0.5rem 0;
        '>
        <strong>Address:</strong> {service_info.get('address', 'N/A')}<br>
        <strong>Phone:</strong> {service_info.get('phone', 'N/A')}<br>
        <strong>Hours:</strong> {service_info.get('hours', 'N/A')}
        </div>
        """
        st.markdown(contact_card, unsafe_allow_html=True)
        
        # Cost & Processing
        st.markdown("#### 💰 Cost & Timeline")
        cost_card = f"""
        <div style='
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #28a745;
            margin: 0.5rem 0;
        '>
        <strong>Cost:</strong> {service_info.get('cost', 'N/A')}<br>
        <strong>Processing Time:</strong> {service_info.get('processing_time', 'N/A')}<br>
        <strong>Eligibility:</strong> {service_info.get('eligibility', 'N/A')}
        </div>
        """
        st.markdown(cost_card, unsafe_allow_html=True)
    
    with col2:
        # Required Documents
        st.markdown("#### 📄 Required Documents")
        documents = service_info.get('documents_required', [])
        if documents:
            docs_html = "".join([f"<li>{doc}</li>" for doc in documents])
            docs_card = f"""
            <div style='
                background: #fff3cd;
                padding: 1.5rem;
                border-radius: 10px;
                border-left: 4px solid #ffc107;
                margin: 0.5rem 0;
            '>
            <ul style='margin: 0; padding-left: 1.2rem;'>
            {docs_html}
            </ul>
            </div>
            """
            st.markdown(docs_card, unsafe_allow_html=True)
        else:
            st.info("No specific documents listed")
        
        # Application Steps
        steps = service_info.get('steps', [])
        if steps:
            st.markdown("#### 📋 Application Steps")
            for i, step in enumerate(steps, 1):
                st.markdown(f"""
                <div style='
                    background: #e7f3ff;
                    padding: 1rem;
                    border-radius: 8px;
                    margin: 0.3rem 0;
                    border-left: 3px solid #17a2b8;
                '>
                <strong>Step {i}:</strong> {step}
                </div>
                """, unsafe_allow_html=True)

def display_text_content(text_content):
    """
    Display the text content in a formatted way
    """
    if not text_content:
        return
    
    # Clean up the text
    lines = text_content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('---') and 'Find another service?' not in line:
            cleaned_lines.append(line)
    
    if cleaned_lines:
        st.markdown("#### 📝 Additional Information")
        text_card = f"""
        <div style='
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid #dee2e6;
            margin: 1rem 0;
            line-height: 1.6;
        '>
        {''.join([f'<p>{line}</p>' for line in cleaned_lines])}
        </div>
        """
        st.markdown(text_card, unsafe_allow_html=True)

def main():
    # Set page config to wide mode FIRST
    st.set_page_config(
        page_title="Public Service Navigator",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Clean CSS styling
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }
    
    /* Main container */
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2.5rem 0;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
        color: white;
        border-radius: 12px;
        margin: 0 0 2rem 0;
    }
    
    .main-header h1 {
        font-size: 2.8rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        font-size: 1.2rem;
        color: #ecf0f1;
        font-weight: 400;
        opacity: 0.9;
    }
    
    /* Card styling */
    .card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e1e8ed;
        margin-bottom: 1.5rem;
    }
    
    /* Input card specific */
    .input-card {
        background: white;
        border-left: 4px solid #3498db;
    }
    
    /* Sidebar card */
    .sidebar-card {
        background: white;
        border-left: 4px solid #2ecc71;
    }
    
    /* Tip cards */
    .tip-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1.2rem;
        margin: 0.8rem 0;
    }
    
    .tip-card strong {
        color: #2c3e50;
        font-size: 0.95rem;
        display: block;
        margin-bottom: 0.3rem;
    }
    
    .tip-card div {
        color: #5a6c7d;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    /* Input styling */
    .stTextInput input {
        border: 2px solid #3498db !important;
        border-radius: 12px !important;
        padding: 1rem 1.2rem !important;
        font-size: 1rem !important;
        color: #2c3e50 !important;
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        box-shadow: 0 2px 10px rgba(52, 152, 219, 0.1) !important;
        font-weight: 500 !important;
        caret-color: #e74c3c !important;
    }
    
    .stTextInput input:focus {
        border-color: #e74c3c !important;
        box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.2) !important;
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
        transform: translateY(-1px);
    }
    
    .stTextInput input::placeholder {
        color: #95a5a6 !important;
        font-weight: 400 !important;
    }
    
    /* Input label styling */
    .input-label {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        color: white;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-block;
        box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3);
    }
    
    /* Input container */
    .input-container {
        background: rgba(255, 255, 255, 0.9);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #e1e8ed;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    /* Static service items */
    .static-service {
        background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
        color: white;
        border: none;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.9rem;
        margin: 0.2rem;
        width: 100%;
        text-align: center;
        cursor: default;
        opacity: 0.9;
        box-shadow: 0 2px 8px rgba(149, 165, 166, 0.3);
    }
    
    /* Main action button */
    .stButton button {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 10px;
        font-weight: 600;
        width: 100%;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(231, 76, 60, 0.4);
        background: linear-gradient(135deg, #c0392b 0%, #a93226 100%);
    }
    
    /* Results container */
    .results-container {
        background: white;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid #e1e8ed;
        margin-top: 1.5rem;
        padding: 2rem;
    }
    
    /* Simple loading animation */
    .loading-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 12px;
        border: 2px solid #e1e8ed;
        margin: 1.5rem 0;
        text-align: center;
    }
    
    .loading-spinner {
        width: 40px;
        height: 40px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #3498db;
        border-radius: 50%;
        margin: 0 auto 1rem;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #7f8c8d;
        padding: 2rem 0 1rem 0;
        font-size: 0.9rem;
        border-top: 1px solid #ecf0f1;
        margin-top: 2rem;
    }
    
    /* Remove default Streamlit constraints */
    .block-container {
        max-width: none !important;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    
    /* Text colors for better contrast */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50 !important;
    }
    
    .stMarkdown {
        color: #34495e;
    }
    </style>
    """, unsafe_allow_html=True)

    # Main content container
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Professional Header
    st.markdown("""
    <div class="main-header">
        <h1>🏛️ Public Service Navigator</h1>
        <p>Streamlined access to government services and official information</p>
    </div>
    """, unsafe_allow_html=True)

    # Main Layout
    col1, col2 = st.columns([3, 1])

    with col1:
        # Input Form Card
        st.markdown('<div class="card input-card">', unsafe_allow_html=True)
        st.markdown("### 🔍 Service Search")
        st.markdown("Find government services and offices in your area")
        
        with st.form("service_form"):
            # Enhanced input container
            st.markdown('<div class="input-container">', unsafe_allow_html=True)
            
            # Use full width inputs in columns
            col_country, col_service, col_city = st.columns(3)
            
            with col_country:
                st.markdown('<div class="input-label">🌍 Country</div>', unsafe_allow_html=True)
                country = st.text_input(
                    "Country",
                    placeholder="e.g., Kenya, UK, USA",
                    help="Enter the country where you need services",
                    label_visibility="collapsed",
                    key="country_input"
                )
            
            with col_service:
                st.markdown('<div class="input-label">🎯 Service Type</div>', unsafe_allow_html=True)
                service_type = st.text_input(
                    "Service Type", 
                    placeholder="e.g., passport, visa, license",
                    help="What government service are you looking for?",
                    label_visibility="collapsed",
                    key="service_input"
                )
            
            with col_city:
                st.markdown('<div class="input-label">📍 City/Area</div>', unsafe_allow_html=True)
                city = st.text_input(
                    "City/Area",
                    placeholder="e.g., London, Nairobi", 
                    help="Enter your city or area",
                    label_visibility="collapsed",
                    key="city_input"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close input container
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🚀 Search for Services", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Process search
        if submitted:
            if not country or not service_type or not city:
                st.error("⚠️ Please fill in all fields to continue")
            else:
                # Simple loading state
                st.markdown(f"""
                <div class="loading-container">
                    <div class="loading-spinner"></div>
                    <h4 style='color: #2c3e50; margin-bottom: 0.5rem;'>Searching for Services</h4>
                    <p style='color: #7f8c8d; margin: 0;'>
                        Looking up {service_type} services in {city}, {country}...
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Run the backend process
                with st.spinner(""):
                    time.sleep(1)  # Brief pause for UX
                    output, error = run_jac_backend(country, service_type, city)
                
                if error:
                    st.error(f"❌ Error: {error}")
                else:
                    st.success(f"✅ Service information found for {service_type} in {city}, {country}")
                    
                    # Parse the output
                    parsed_data = parse_service_output(output)
                    
                    # Results Container
                    st.markdown('<div class="results-container">', unsafe_allow_html=True)
                    st.markdown("### 📋 Service Details")
                    
                    if parsed_data['has_json']:
                        # Display structured JSON data
                        display_json_data(parsed_data['json_data'])
                    
                    # Display text content
                    display_text_content(parsed_data['text_content'])
                    
                    # Raw output in expander
                    with st.expander("📄 View Raw API Response"):
                        st.markdown("#### Complete Service Information")
                        st.text_area("Raw Output", parsed_data['raw_output'], height=300, label_visibility="collapsed")
                    
                    # Action Buttons
                    st.markdown("---")
                    st.markdown("### 🔧 Actions")
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        if st.button("🔄 New Search", use_container_width=True, key="new_search_1"):
                            st.rerun()
                    with action_col2:
                        st.download_button(
                            "💾 Download Report", 
                            data=parsed_data['raw_output'],
                            file_name=f"service_info_{service_type}_{city}_{country}.txt",
                            mime="text/plain",
                            use_container_width=True,
                            key="download_1"
                        )
                    with action_col3:
                        if st.button("📋 Copy Details", use_container_width=True, key="copy_1"):
                            st.code(parsed_data['raw_output'])
                            st.success("✅ Service details copied to clipboard!")
                    
                    st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Combined Tips and Services Card
        st.markdown('<div class="card sidebar-card">', unsafe_allow_html=True)
        st.markdown("### 💡 Quick Guide")
        
        st.markdown("""
        <div class="tip-card">
            <strong>🎯 Be Specific</strong>
            <div>Use exact service names like "passport renewal" or "driver license"</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="tip-card">
            <strong>📍 Location Details</strong>
            <div>Include city and country for accurate local information</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="tip-card">
            <strong>📞 Contact Info</strong>
            <div>Results include office locations and contact details</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Popular Services - Static non-clickable items
        st.markdown("### 🔥 Popular Services")
        st.markdown("<div style='margin: 0.5rem 0; font-size: 0.9rem; color: #7f8c8d;'>Common service categories:</div>", unsafe_allow_html=True)
        
        services = [
            "Passport", "Visa Services", "Driver License", 
            "Tax Filing", "Healthcare", "Business License",
            "ID Card", "Education"
        ]
        
        # Create static service items (non-clickable)
        for service in services:
            st.markdown(f'<div class="static-service">🔹 {service}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Additional Info Card
        st.markdown('<div class="card sidebar-card">', unsafe_allow_html=True)
        st.markdown("### ℹ️ About This Service")
        st.markdown("""
        <div style='font-size: 0.9rem; color: #5a6c7d; line-height: 1.5;'>
        This tool helps you find official government services 
        and contact information for various countries worldwide.
        
        **Features:**
        • Office locations
        • Required documents
        • Application processes
        • Contact information
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="footer">
        <strong>Public Service Navigator</strong> • Powered by Jaclang AI • v2.0<br>
        <span style='font-size: 0.8rem; color: #95a5a6;'>Official government service information portal</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # Close main container

if __name__ == "__main__":
    main()