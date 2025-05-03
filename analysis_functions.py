import os
import json
import streamlit as st
from euriai import EuriaiClient
from dotenv import load_dotenv

load_dotenv()


EURIAI_API_KEY = os.getenv("EURIAI_API_KEY")


def analyze_video_with_openai(video_url, video_metadata, language="English"):
    """Analyze video content with platform-specific optimization using OpenAI."""
    # Check if API key is available
    if not os.getenv("EURIAI_API_KEY"):
        raise Exception("API key is required for analysis")

    # Initialize the client
    client = EuriaiClient(model="gpt-4.1-nano", api_key=EURIAI_API_KEY)

    platform = video_metadata.get("platform", "YouTube")

    analysis_prompt = f"""
    Analyze the {platform} video at {video_url} with title "{video_metadata.get("title", "")}".
    
    Provide a detailed analysis including:
    1. A summary of the video content (based on the title and any metadata)
    2. Main topics likely covered (at least 5 specific topics)
    3. Emotional tone and style of the video
    4. Target audience demographics and interests
    5. Content structure and flow
    
    Your analysis should be in {language} language.
    Make reasonable assumptions based on the available information.
    """

    analysis_response = client.generate_completion(
        # model="gpt-4",
        prompt=[
            {
                "role": "system",
                "content": f"You are a video content analyst specialized in understanding {platform} video content, structure, and audience appeal. You are fluent in {language} and will provide all output in {language}.",
            },
            {"role": "user", "content": analysis_prompt},
        ],
        temperature=0.7,
    )
    analysis_result = analysis_response.choices[0].message.content

    # Step 2: SEO Recommendations
    duration = video_metadata.get("duration", 0)
    minutes = duration // 60
    num_timestamps = min(15, max(5, int(minutes / 2))) if minutes > 0 else 5

    seo_prompt = f"""
    Based on this analysis of a {platform} video titled "{video_metadata.get("title", "")}":
    
    {analysis_result}
    
    Generate comprehensive SEO recommendations optimized specifically for {platform} including:
    
    1. EXACTLY 35 trending hashtags/tags related to the video content, ranked by potential traffic and relevance. 
       For {platform}, optimize the tags according to platform best practices.
    
    2. Detailed and SEO-optimized video description (400-500 words) that includes:
       - An engaging hook in the first 2-3 sentences that entices viewers
       - A clear value proposition explaining what viewers will gain
       - Key topics covered with strategic keyword placement
       - A strong call-to-action appropriate for {platform}
       - Essential links (placeholder)
       - Proper formatting with paragraph breaks for readability
    
    3. Exactly {num_timestamps} timestamps with descriptive labels evenly distributed throughout the video (duration: {duration} seconds)
    
    4. 5-7 alternative title suggestions ranked by SEO potential, each under 60 characters for YouTube or appropriate length for {platform}
    
    Format your response as JSON with the following structure:
    {{
        "tags": ["tag1", "tag2", ...],  // EXACTLY 35 tags total
        "description": "Complete optimized description here...",
        "timestamps": [
            {{"time": "00:00", "description": "Detailed segment description"}},
            ...
        ],
        "titles": [
            {{"rank": 1, "title": "Best title with keywords", "reason": "Why this title works well"}}
            ...
        ]
    }}
    
    All content should be in {language} language.
    Return ONLY the valid JSON with no explanation or other text.
    """

    seo_response = client.generate_completion(
        # model="gpt-4",
        prompt=[
            {
                "role": "system",
                "content": f"You are an SEO specialist focusing on optimizing {platform} content for maximum discovery and engagement. You are fluent in {language} and will provide all output in {language}.",
            },
            {"role": "user", "content": seo_prompt},
        ],
        temperature=0.7,
    )

    seo_result_text = seo_response.choices[0].message.content

    # Parse JSON from the SEO response
    try:
        seo_result = json.loads(seo_result_text)

        # Ensure we have exactly 35 tags
        if len(seo_result.get("tags", [])) != 35:
            seo_result["tags"] = ensure_exactly_35_tags(
                seo_result.get("tags", []), client, video_metadata, platform, language
            )

    except json.JSONDecodeError:
        # Try to extract JSON from the text if it's not pure JSON
        try:
            json_start = seo_result_text.find("{")
            json_end = seo_result_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                seo_result = json.loads(seo_result_text[json_start:json_end])
            else:
                # Generate a fallback JSON structure
                seo_result = generate_fallback_seo(video_metadata, platform, language)
        except:
            seo_result = generate_fallback_seo(video_metadata, platform, language)

    # Step 3: Thumbnail Concepts
    thumbnail_prompt = f"""
    Based on this analysis of a {platform} video titled "{video_metadata.get("title", "")}":
    
    {analysis_result}
    
    Create 3 detailed thumbnail concepts specifically optimized for {platform}.
    
    For each concept, provide:
    1. The main visual elements to include (very specific and detailed)
    2. Text overlay suggestions (maximum 3-5 words, optimized for {platform})
    3. Color scheme (with exact hex codes for 3 colors)
    4. Focal point/main subject (detailed description of what should be the center of attention)
    5. Emotional tone the thumbnail should convey
    6. Composition details (layout, text placement, foreground/background elements)
    
    Format your response as JSON with the following structure:
    {{
        "thumbnail_concepts": [
            {{
                "concept": "Detailed description of concept 1",
                "text_overlay": "Short engaging text",
                "colors": ["#hexcode1", "#hexcode2", "#hexcode3"],
                "focal_point": "Specific description of focal element",
                "tone": "Emotional tone",
                "composition": "Layout and placement details"
            }},
            ...
        ]
    }}
    
    All content should be in {language} language.
    Return ONLY the valid JSON with no explanation.
    """

    thumbnail_response = client.generate_completion(
        # model="gpt-4",
        prompt=[
            {
                "role": "system",
                "content": f"You are a professional thumbnail designer specialized in creating engaging {platform} thumbnails that maximize click-through rates. You understand the specific requirements and best practices for {platform} thumbnails. You are fluent in {language} and will provide all output in {language}.",
            },
            {"role": "user", "content": thumbnail_prompt},
        ],
        temperature=0.7,
    )

    thumbnail_result_text = thumbnail_response.choices[0].message.content

    # Parse JSON from the thumbnail response
    try:
        thumbnail_result = json.loads(thumbnail_result_text)
    except json.JSONDecodeError:
        # Try to extract JSON from the text if it's not pure JSON
        try:
            json_start = thumbnail_result_text.find("{")
            json_end = thumbnail_result_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                thumbnail_result = json.loads(
                    thumbnail_result_text[json_start:json_end]
                )
            else:
                thumbnail_result = generate_fallback_thumbnails(platform, language)
        except:
            thumbnail_result = generate_fallback_thumbnails(platform, language)

    return {
        "analysis": analysis_result,
        "seo": seo_result,
        "thumbnails": thumbnail_result,
    }


def ensure_exactly_35_tags(tags, client, video_metadata, platform, language):
    """Ensure we have exactly 35 tags by adding or removing tags as needed."""
    current_count = len(tags)

    if current_count == 35:
        return tags

    if current_count < 35:
        # Generate more tags based on existing ones
        more_tags_prompt = f"""
        Based on these existing tags for a {platform} video about "{video_metadata.get("title", "")}":
        {tags}
        
        Generate {35 - current_count} additional relevant and trending tags in {language}.
        Return ONLY a JSON array with the new tags, no explanations.
        """

        try:
            more_tags_response = client.generate_completion(
                # model="gpt-4",
                prompt=[{"role": "user", "content": more_tags_prompt}],
                temperature=0.7,
            )

            additional_tags = json.loads(more_tags_response.choices[0].message.content)
            tags.extend(additional_tags[: 35 - current_count])
        except:
            # Add generic tags if JSON parsing fails
            for i in range(current_count, 35):
                tags.append(f"related_tag_{i}")

    elif current_count > 35:
        # Truncate to exactly 35
        tags = tags[:35]

    return tags


def generate_fallback_seo(video_metadata, platform, language):
    """Generate fallback SEO content if API fails."""
    title = video_metadata.get("title", "Video Title")

    # Generate 35 YouTube-specific tags
    youtube_tags = [
        "youtube",
        "video",
        "tutorial",
        "vlog",
        "howto",
        "review",
        "explained",
        "educational",
        "learn",
        "step by step",
        "beginner",
        "advanced",
        "masterclass",
        "course",
        "lesson",
        "strategy",
        "technique",
        "demonstration",
        "walkthrough",
        "overview",
        "comparison",
        "versus",
        "top",
        "best",
        "recommended",
        "trending",
        "viral",
        "popular",
        "interesting",
        "amazing",
        "helpful",
        "useful",
        "informative",
        "detailed",
        "comprehensive",
    ]

    return {
        "tags": youtube_tags,
        "description": f"This YouTube video about {title} provides valuable information and insights. Watch to learn more about this topic.\n\nDon't forget to like, comment, and subscribe for more content!\n\n#YouTube #Tutorial",
        "timestamps": [{"time": "00:00", "description": "Introduction"}],
        "titles": [
            {"rank": 1, "title": title, "reason": "Original title"},
            {
                "rank": 2,
                "title": f"Complete Guide to {title}",
                "reason": "Informative variant",
            },
            {
                "rank": 3,
                "title": f"How to {title} | Step by Step Tutorial",
                "reason": "Tutorial style",
            },
            {
                "rank": 4,
                "title": f"Top 10 {title} Tips You Need to Know",
                "reason": "List format",
            },
            {
                "rank": 5,
                "title": f"{title} Explained Simply",
                "reason": "Educational angle",
            },
        ],
    }


def generate_fallback_thumbnails(platform, language):
    """Generate fallback thumbnail concepts if API fails."""
    youtube_colors = ["#FF0000", "#FFFFFF", "#000000"]  # YouTube colors

    return {
        "thumbnail_concepts": [
            {
                "concept": "Professional YouTube thumbnail with text overlay",
                "text_overlay": "Ultimate Guide",
                "colors": youtube_colors,
                "focal_point": "Center of the image with clear subject",
                "tone": "Professional and educational",
                "composition": "Subject on the right, text on the left with high contrast",
            },
            {
                "concept": "Emotional reaction thumbnail with facial expression",
                "text_overlay": "You Won't Believe This!",
                "colors": youtube_colors,
                "focal_point": "Close-up of surprised face or reaction",
                "tone": "Surprising and emotionally engaging",
                "composition": "Face taking up 40% of thumbnail with text above",
            },
            {
                "concept": "Before/After comparison thumbnail",
                "text_overlay": "Transformation",
                "colors": youtube_colors,
                "focal_point": "Split screen showing clear contrast",
                "tone": "Impressive and motivational",
                "composition": "50/50 split with arrow or divider in the middle",
            },
        ]
    }
