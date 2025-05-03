import os
import streamlit as st
from dotenv import load_dotenv
import json
import time
import tempfile
from PIL import Image
from io import BytesIO
import requests
from euriai import EuriaiClient

# Import the utility functions
from utils.video_extractor import get_video_metadata
from utils.seo_agents import run_seo_analysis_with_langchain
from utils.thumbnails import generate_thumbnail_with_dalle, create_thumbnail_preview

import warnings

# Ignore all warnings
warnings.filterwarnings("ignore")

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Configure API keys from environment
EURIAI_API_KEY = os.getenv("EURIAI_API_KEY")

# Available languages
LANGUAGES = [
    "English",
    "Spanish",
    "French",
    "German",
    "Italian",
    "Portuguese",
    "Hindi",
    "Japanese",
    "Korean",
    "Chinese",
    "Russian",
    "Arabic",
]

# Set page config
st.set_page_config(
    page_title="Video SEO Optimizer", layout="wide", initial_sidebar_state="expanded"
)

# Apply custom CSS styling
st.markdown(
    """
<style>
    .main-title { font-size: 2.5rem; color: #1E88E5; margin-bottom: 1rem; }
    .section-title { font-size: 1.5rem; color: #0D47A1; margin-top: 1rem; }
    .tag-pill { background-color: #E3F2FD; color: #1565C0; padding: 5px 10px; border-radius: 15px; margin: 2px; display: inline-block; }
    .timestamp-card { background-color: #2196F3; padding: 10px; border-radius: 5px; margin-bottom: 5px; color: #FFFFFF; }
    .timestamp-card b { color: #FF5252; font-weight: bold; }
    .stButton>button { background-color: #1E88E5; color: white; }
    .platform-badge { font-weight: bold; padding: 5px 10px; border-radius: 5px; display: inline-block; margin-bottom: 10px; }
    .youtube-badge { background-color: #FF0000; color: white; }
    .thumbnail-concept { border: 1px solid #DDDDDD; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
    .color-swatch { height: 25px; width: 25px; display: inline-block; margin-right: 5px; border: 1px solid #CCCCCC; }
</style>
""",
    unsafe_allow_html=True,
)


# Sidebar for API keys and info
with st.sidebar:
    st.image("https://via.placeholder.com/150x150.png?text=SEO+Agent", width=150)
    st.title("API Configuration")

    EURIAI_API_KEY = st.text_input(
        "EURI API Key", type="password", key="EURIAI_API_KEY"
    )

    # Save API key to environment if provided
    if EURIAI_API_KEY:
        os.environ["EURIAI_API_KEY"] = EURIAI_API_KEY

    st.divider()

    # Language selection
    st.subheader("Language Settings")
    selected_language = st.selectbox("Select Output Language", LANGUAGES, index=0)

    # Model options
    st.subheader("Model Settings")
    model_option = st.selectbox(
        "Select AI Engine",
        ["EURI GPT-4", "LangChain Agent"],
        index=1,
        help="Choose between direct EURI API calls or a LangChain agent system",
    )

    st.divider()
    st.subheader("About")
    st.write("""
    This tool uses AI to analyze videos and generate platform-specific SEO recommendations.
    
    It optimizes:
    - 35 Trending Tags
    - Detailed Descriptions
    - Strategic Timestamps
    - 5+ SEO-friendly Titles
    - Platform-optimized Thumbnails
    """)

    st.divider()
    st.caption("Created with OpenAI GPT-4, LangChain & Streamlit")


# Main content
st.markdown(
    "<h1 class='main-title'>Video SEO Optimizer Pro</h1>", unsafe_allow_html=True
)
st.write(
    "Analyze videos from YouTube to generate platform-specific SEO recommendations."
)


# Video URL input
video_url = st.text_input(
    "Enter video URL", placeholder="https://www.youtube.com/watch?v=..."
)


# Initialize session state for storing results
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "video_metadata" not in st.session_state:
    st.session_state.video_metadata = None
if "video_url" not in st.session_state:
    st.session_state.video_url = ""

# Process the URL if provided
if video_url:
    st.session_state.video_url = video_url
    try:
        with st.spinner("Fetching video information..."):
            metadata = get_video_metadata(video_url)
            st.session_state.video_metadata = metadata

        # Display video information
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Video Details")

            # Display platform badge
            platform = metadata.get("platform", "Unknown")
            badge_class = (
                f"{platform.lower()}-badge"
                if platform in ["YouTube", "Instagram", "LinkedIn"]
                else ""
            )
            st.markdown(
                f"<div class='platform-badge {badge_class}'>{platform}</div>",
                unsafe_allow_html=True,
            )

            st.write(f"**Title:** {metadata.get('title', 'N/A')}")

            if metadata.get("author"):
                st.write(f"**Creator:** {metadata.get('author', 'N/A')}")

            if metadata.get("duration"):
                minutes = metadata.get("duration") // 60
                seconds = metadata.get("duration") % 60
                st.write(f"**Duration:** {minutes}m {seconds}s")

            if metadata.get("views"):
                st.write(f"**Views:** {metadata.get('views', 0):,}")

        with col2:
            if metadata.get("thumbnail_url"):
                st.image(
                    metadata.get("thumbnail_url"),
                    caption="Current Thumbnail",
                    use_column_width=True,
                )

        # Run analysis button with language selection
        st.write(
            f"Analysis will be performed in **{selected_language}** using **{model_option}**"
        )
        if st.button(f"Generate SEO Recommendations"):
            if not os.getenv("EURIAI_API_KEY"):
                st.error("Please enter your OpenAI API key in the sidebar.")
            else:
                with st.spinner(
                    f"Analyzing video content and generating optimized SEO recommendations in {selected_language}..."
                ):
                    try:
                        # Run analysis using LangChain Agents
                        if model_option == "LangChain Agent":
                            results = run_seo_analysis_with_langchain(
                                video_url,
                                st.session_state.video_metadata,
                                language=selected_language,
                            )
                        else:
                            # Import the direct OpenAI approach
                            from analysis_functions import analyze_video_with_openai

                            results = analyze_video_with_openai(
                                video_url,
                                st.session_state.video_metadata,
                                language=selected_language,
                            )

                        # Store results in session state
                        st.session_state.analysis_results = results
                        st.session_state.analysis_complete = True

                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")

    except Exception as e:
        st.error(f"Error processing video URL: {str(e)}")

# Display results if analysis is complete
if st.session_state.analysis_complete and st.session_state.analysis_results:
    results = st.session_state.analysis_results

    st.success("Analysis complete! Here are your SEO recommendations:")

    # Create tabs for different sections
    tabs = st.tabs(
        [
            "Content Analysis",
            "Tags (35)",
            "Description",
            "Timestamps",
            "Titles (5+)",
            "Thumbnails",
        ]
    )

    # Content Analysis Tab
    with tabs[0]:
        st.markdown(
            "<h2 class='section-title'>Content Analysis</h2>", unsafe_allow_html=True
        )
        st.write(results["analysis"])

    # Tags Tab
    with tabs[1]:
        st.markdown(
            "<h2 class='section-title'>35 Recommended Tags</h2>", unsafe_allow_html=True
        )
        st.write("Use these trending tags to improve your video's discoverability:")

        # Display tags in a grid
        tag_columns = st.columns(3)
        tags = results["seo"]["tags"]
        tags_per_column = len(tags) // 3 + (1 if len(tags) % 3 > 0 else 0)

        for i, col in enumerate(tag_columns):
            with col:
                for j in range(
                    i * tags_per_column, min((i + 1) * tags_per_column, len(tags))
                ):
                    if j < len(tags):
                        st.markdown(
                            f"<div class='tag-pill'>#{tags[j]}</div>",
                            unsafe_allow_html=True,
                        )

        # Tag metrics
        st.info(
            f"Total tags: {len(tags)} - Optimized for {st.session_state.video_metadata.get('platform', 'YouTube')}"
        )

        # Copy tags button
        if st.button("Copy All Tags"):
            tags_text = " ".join([f"#{tag}" for tag in tags])
            st.code(tags_text)
            st.success("Tags copied! Use ctrl+C to copy to clipboard.")

    # Description Tab
    with tabs[2]:
        st.markdown(
            "<h2 class='section-title'>Platform-Optimized Description</h2>",
            unsafe_allow_html=True,
        )
        st.write(
            f"Use this SEO-optimized description for your {st.session_state.video_metadata.get('platform', 'YouTube')} video:"
        )

        description = results["seo"]["description"]
        st.text_area("Copy this description", description, height=300)

        # Word count and character metrics
        word_count = len(description.split())
        char_count = len(description)
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Word count: {word_count} words")
        with col2:
            st.info(f"Character count: {char_count} characters")

    # Timestamps Tab
    with tabs[3]:
        st.markdown(
            "<h2 class='section-title'>Video Timestamps</h2>", unsafe_allow_html=True
        )
        st.write("Add these timestamps to your description to improve user navigation:")

        timestamps = results["seo"]["timestamps"]
        timestamp_text = ""

        for ts in timestamps:
            st.markdown(
                f"<div class='timestamp-card'><b>{ts['time']}</b> - {ts['description']}</div>",
                unsafe_allow_html=True,
            )
            timestamp_text += f"{ts['time']} - {ts['description']}\n"

        # Timestamp metrics
        st.info(
            f"Total timestamps: {len(timestamps)} - Optimized for a {st.session_state.video_metadata.get('duration', 0) // 60} minute video"
        )

        # Copy timestamps button
        if st.button("Copy All Timestamps"):
            st.code(timestamp_text)
            st.success("Timestamps copied! Use ctrl+C to copy to clipboard.")

        # Information about using timestamps
        st.markdown("""
        **How to use timestamps in YouTube:**
        1. Copy these timestamps to your video description
        2. Make sure each timestamp is on a new line 
        3. The format must be exactly as shown (00:00 - Description)
        4. Timestamps will automatically become clickable links in YouTube
        
        **Benefits of using timestamps:**
        - Improved user experience and navigation
        - Increased watch time and engagement
        - Better visibility in YouTube search
        - More professional appearance
        """)

    # Titles Tab
    with tabs[4]:
        st.markdown(
            "<h2 class='section-title'>Title Suggestions</h2>", unsafe_allow_html=True
        )
        st.write("Try these title options to improve click-through rate:")

        titles = results["seo"]["titles"]
        for title in titles:
            col1, col2 = st.columns([1, 5])
            with col1:
                st.markdown(f"<h3>#{title['rank']}</h3>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<h3>{title['title']}</h3>", unsafe_allow_html=True)

                # Show reasoning if available
                if "reason" in title:
                    st.markdown(f"<i>{title['reason']}</i>", unsafe_allow_html=True)

                # Character count with platform-specific limit
                char_count = len(title["title"])
                platform = st.session_state.video_metadata.get("platform", "YouTube")
                char_limit = 60 if platform == "YouTube" else 100
                status = "✅ Good length" if char_count <= char_limit else "⚠️ Too long"
                st.write(f"{char_count}/{char_limit} characters - {status}")

    # Thumbnails Tab
    with tabs[5]:
        st.markdown(
            "<h2 class='section-title'>AI-Generated Thumbnail Concepts</h2>",
            unsafe_allow_html=True,
        )
        platform = st.session_state.video_metadata.get("platform", "YouTube")
        st.write(f"Here are thumbnail concepts specifically designed for {platform}:")

        thumbnail_concepts = results["thumbnails"]["thumbnail_concepts"]

        for i, concept in enumerate(thumbnail_concepts):
            st.markdown(f"<div class='thumbnail-concept'>", unsafe_allow_html=True)
            st.markdown(
                f"### Concept {i + 1}: {concept.get('text_overlay', 'Concept')}"
            )

            col1, col2 = st.columns([3, 2])
            with col1:
                st.write(f"**Concept:** {concept.get('concept', 'N/A')}")
                st.write(f"**Text Overlay:** {concept.get('text_overlay', 'N/A')}")

                # Display color swatches
                if "colors" in concept and isinstance(concept["colors"], list):
                    st.write("**Colors:**")
                    color_html = ""
                    for color in concept["colors"]:
                        color_html += f"<div class='color-swatch' style='background-color: {color};'></div>"
                    st.markdown(color_html, unsafe_allow_html=True)
                    st.write(", ".join(concept["colors"]))

                st.write(f"**Focal Point:** {concept.get('focal_point', 'N/A')}")
                st.write(f"**Emotional Tone:** {concept.get('tone', 'N/A')}")

                # Display additional fields if available
                if "composition" in concept:
                    st.write(f"**Composition:** {concept['composition']}")

            with col2:
                # Generate thumbnail with DALL-E if OpenAI API key is available
                if os.getenv("EURIAI_API_KEY"):
                    try:
                        # Check if we already generated this thumbnail
                        cache_key = f"thumbnail_{i}_{st.session_state.video_metadata.get('video_id', '')}"

                        if cache_key not in st.session_state:
                            # Show generation in progress
                            with st.spinner("Generating AI thumbnail..."):
                                # Only generate if we have enough context
                                if (
                                    len(concept.get("concept", "")) > 10
                                    and len(results["analysis"]) > 100
                                ):
                                    # Create OpenAI client
                                    # client = OpenAI(
                                    #     api_key=os.environ.get("OPENAI_API_KEY")
                                    # )

                                    client = EuriaiClient(
                                        api_key=os.getenv("EURIAI_API_KEY"),
                                        model="gemini-2.5-pro-exp-03-25",
                                    )

                                    # Generate the thumbnail
                                    image_url = generate_thumbnail_with_dalle(
                                        client,
                                        concept,
                                        st.session_state.video_metadata.get(
                                            "title", ""
                                        ),
                                        platform,
                                    )

                                    # Store in session state
                                    if image_url:
                                        st.session_state[cache_key] = image_url
                                    else:
                                        # Use fallback visualization
                                        st.session_state[cache_key] = None
                                else:
                                    st.session_state[cache_key] = None

                        # Display the image if we have one
                        if st.session_state.get(cache_key):
                            st.image(
                                st.session_state[cache_key],
                                caption=f"AI-generated thumbnail for concept {i + 1}",
                            )

                            # Add download button for the image
                            if st.button(
                                f"Download Thumbnail {i + 1}", key=f"download_thumb_{i}"
                            ):
                                response = requests.get(st.session_state[cache_key])
                                image = Image.open(BytesIO(response.content))

                                # Convert to bytes
                                buf = BytesIO()
                                image.save(buf, format="PNG")
                                byte_im = buf.getvalue()

                                # Provide download button
                                st.download_button(
                                    label=f"Save Thumbnail {i + 1}",
                                    data=byte_im,
                                    file_name=f"thumbnail_{i + 1}.png",
                                    mime="image/png",
                                    key=f"save_thumb_{i}",
                                )
                        else:
                            # Use thumbnail preview from the thumbnails module
                            preview = create_thumbnail_preview(
                                concept,
                                st.session_state.video_metadata.get("title", ""),
                            )

                            # Convert PIL image to bytes for display
                            buf = BytesIO()
                            preview.save(buf, format="PNG")
                            byte_im = buf.getvalue()

                            st.image(byte_im, caption="Thumbnail preview")
                    except Exception as e:
                        st.warning(f"Could not generate thumbnail with DALL-E: {e}")
                        # Create a simple colored preview
                        preview = create_thumbnail_preview(
                            concept, st.session_state.video_metadata.get("title", "")
                        )
                        buf = BytesIO()
                        preview.save(buf, format="PNG")
                        st.image(buf.getvalue())
                else:
                    st.info(
                        "Add your OpenAI API key to generate AI thumbnails with DALL-E"
                    )
                    # Show a basic preview without DALL-E
                    preview = create_thumbnail_preview(
                        concept, st.session_state.video_metadata.get("title", "")
                    )
                    buf = BytesIO()
                    preview.save(buf, format="PNG")
                    st.image(buf.getvalue(), caption="Basic thumbnail preview")

                # Regenerate button
                if os.getenv("EURIAI_API_KEY"):
                    cache_key = f"thumbnail_{i}_{st.session_state.video_metadata.get('video_id', '')}"
                    if st.button(
                        f"Regenerate Thumbnail {i + 1}", key=f"regen_thumb_{i}"
                    ):
                        with st.spinner("Generating new thumbnail..."):
                            # Create OpenAI client
                            # client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

                            client = EuriaiClient(
                                api_key=os.getenv("EURIAI_API_KEY"),
                                model="gemini-2.5-pro-exp-03-25",
                            )

                            # Generate the thumbnail
                            image_url = generate_thumbnail_with_dalle(
                                client,
                                concept,
                                st.session_state.video_metadata.get("title", ""),
                                platform,
                            )

                            # Store in session state
                            if image_url:
                                st.session_state[cache_key] = image_url
                                st.experimental_rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        # Additional thumbnail info
        platform = st.session_state.video_metadata.get("platform", "YouTube")
        st.info(
            f"{platform} thumbnails are optimized for the platform's recommended dimensions"
        )

        # Note about DALL-E
        st.markdown("""
        **About AI-generated thumbnails:** The thumbnails are generated using OpenAI's DALL-E model based on your video's content analysis. 
        Each thumbnail includes the suggested text overlay directly on the image. These are ready-to-use thumbnails that you can download and upload directly to your video platform.
        """)

# Help section
with st.expander("How to Use This Tool"):
    st.write("""
    ## Getting Started
    
    1. **Enter API Keys**: Add your OpenAI API key in the sidebar
    2. **Select Language**: Choose your preferred output language
    3. **Choose AI Engine**: Select between OpenAI GPT-4 directly or LangChain Agent
    4. **Enter Video URL**: Paste a YouTube video URL
    5. **Generate Recommendations**: Click the button to analyze the video
    6. **Use the Results**: Copy and implement the SEO recommendations
    
    ## Features
    
    - **Content Analysis**: AI-powered understanding of your video's topics and structure
    - **35 Tags**: Trending and relevant tags to improve discovery
    - **Platform-Specific Description**: SEO-optimized description with keywords and calls to action
    - **Smart Timestamps**: Strategic timestamps to improve user navigation and watch time
    - **5+ Title Options**: Alternative title suggestions ranked by SEO potential
    - **Platform-Optimized Thumbnails**: Thumbnail concepts designed for your specific platform
    """)

# Footer
st.divider()
st.caption(
    "Video SEO Optimizer Pro • Multilingual Optimization • Platform-Specific Recommendations"
)
