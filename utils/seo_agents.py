from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.agents import (
    Tool,
    AgentExecutor,
    LLMSingleActionAgent,
    AgentOutputParser,
)
from langchain.schema import AgentAction, AgentFinish, HumanMessage, SystemMessage
import json
import re
import os

from dotenv import load_dotenv

load_dotenv()

from euriai import EuriaiLangChainLLM

EURIAI_API_KEY = os.getenv("EURIAI_API_KEY")


# Define response schemas for structured output
def get_seo_output_parser():
    """Create a structured output parser for SEO recommendations."""
    response_schemas = [
        ResponseSchema(
            name="tags",
            description="A list of exactly 35 relevant hashtags/tags for the video",
        ),
        ResponseSchema(
            name="description",
            description="An SEO-optimized video description between 400-500 words",
        ),
        ResponseSchema(
            name="timestamps",
            description="A list of timestamp objects with 'time' and 'description' fields more the 5 timestamps of the video",
        ),
        ResponseSchema(
            name="titles",
            description="A list of title suggestion objects with 'rank', 'title', and 'reason' fields",
        ),
    ]
    return StructuredOutputParser.from_response_schemas(response_schemas)


def get_thumbnail_output_parser():
    """Create a structured output parser for thumbnail recommendations."""
    response_schemas = [
        ResponseSchema(
            name="thumbnail_concepts",
            description="A list of 3 thumbnail concept objects with all required fields",
        )
    ]
    return StructuredOutputParser.from_response_schemas(response_schemas)


def run_seo_analysis_with_langchain(video_url, video_metadata, language="English"):
    """Run a complete SEO analysis using LangChain agents."""
    if not os.getenv("EURIAI_API_KEY"):
        raise Exception("EURIAI API key is required for analysis")

    # Initialize ChatOpenAI model
    llm = EuriaiLangChainLLM(
        api_key=EURIAI_API_KEY, model="gpt-4.1-nano", temperature=0.7, max_tokens=1000
    )

    # Setup for analysis
    platform = video_metadata.get("platform", "YouTube")
    title = video_metadata.get("title", "")
    duration = video_metadata.get("duration", 0)
    minutes = duration // 60
    num_timestamps = min(15, max(5, int(minutes / 2))) if minutes > 0 else 5

    # Step 1: Video content analysis
    analysis_template = """
    You are a video content analyst specialized in understanding {platform} videos, their structure, and audience appeal.
    
    Analyze the {platform} video at {video_url} with title "{title}".
    
    Provide a detailed analysis including:
    1. A summary of the video content (based on the title and any metadata)
    2. Main topics likely covered (at least 5 specific topics)
    3. Emotional tone and style of the video
    4. Target audience demographics and interests
    5. Content structure and flow
    
    Your analysis should be in {language} language.
    Make reasonable assumptions based on the available information.
    """

    analysis_prompt = PromptTemplate(
        input_variables=["platform", "video_url", "title", "language"],
        template=analysis_template,
    )

    analysis_chain = LLMChain(llm=llm, prompt=analysis_prompt)

    analysis_result = analysis_chain.run(
        platform=platform, video_url=video_url, title=title, language=language
    )

    # Step 2: SEO recommendations
    seo_output_parser = get_seo_output_parser()
    seo_format_instructions = seo_output_parser.get_format_instructions()

    seo_template = """
    You are an SEO specialist focusing on optimizing {platform} content for maximum discovery and engagement.
    
    Based on this analysis of a {platform} video titled "{title}":
    
    {analysis}
    
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
    
    {format_instructions}
    
    All content should be in {language} language.
    """

    seo_prompt = PromptTemplate(
        input_variables=[
            "platform",
            "title",
            "analysis",
            "num_timestamps",
            "duration",
            "language",
        ],
        partial_variables={"format_instructions": seo_format_instructions},
        template=seo_template,
    )

    seo_chain = LLMChain(llm=llm, prompt=seo_prompt)

    seo_result = seo_chain.run(
        platform=platform,
        title=title,
        analysis=analysis_result,
        num_timestamps=num_timestamps,
        duration=duration,
        language=language,
    )

    # Parse the SEO results
    try:
        # Try to extract JSON from the text
        seo_data = parse_langchain_output(seo_result)

        # Ensure we have exactly 35 tags
        if len(seo_data.get("tags", [])) != 35:
            # Call helper function to generate more tags if needed
            seo_data["tags"] = ensure_35_tags(
                seo_data.get("tags", []), llm, title, platform, language
            )
    except Exception:
        # Fallback to basic structure if parsing fails
        seo_data = generate_fallback_seo(title, platform, language)

    # Step 3: Thumbnail concepts
    thumbnail_output_parser = get_thumbnail_output_parser()
    thumbnail_format_instructions = thumbnail_output_parser.get_format_instructions()

    thumbnail_template = """
    You are a professional thumbnail designer specialized in creating engaging {platform} thumbnails that maximize click-through rates.
    
    Based on this analysis of a {platform} video titled "{title}":
    
    {analysis}
    
    Create 3 detailed thumbnail concepts specifically optimized for {platform}.
    
    For each concept, provide:
    1. The main visual elements to include (very specific and detailed)
    2. Text overlay suggestions (maximum 3-5 words, optimized for {platform})
    3. Color scheme (with exact hex codes for 3 colors)
    4. Focal point/main subject (detailed description of what should be the center of attention)
    5. Emotional tone the thumbnail should convey
    6. Composition details (layout, text placement, foreground/background elements)
    
    {format_instructions}
    
    All content should be in {language} language.
    """

    thumbnail_prompt = PromptTemplate(
        input_variables=["platform", "title", "analysis", "language"],
        partial_variables={"format_instructions": thumbnail_format_instructions},
        template=thumbnail_template,
    )

    thumbnail_chain = LLMChain(llm=llm, prompt=thumbnail_prompt)

    thumbnail_result = thumbnail_chain.run(
        platform=platform, title=title, analysis=analysis_result, language=language
    )

    # Parse the thumbnail results
    try:
        # Try to extract JSON from the text
        thumbnail_data = parse_langchain_output(thumbnail_result)
    except Exception:
        # Fallback to basic structure if parsing fails
        thumbnail_data = generate_fallback_thumbnails(platform, language)

    # Return the combined results
    return {"analysis": analysis_result, "seo": seo_data, "thumbnails": thumbnail_data}


def parse_langchain_output(output_text):
    """Parse the output from LangChain, handling various formats."""
    # First, try to parse as pure JSON
    try:
        return json.loads(output_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        json_pattern = r"```json\s*([\s\S]*?)\s*```"
        match = re.search(json_pattern, output_text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to extract JSON from the text using regex patterns
        json_start = output_text.find("{")
        json_end = output_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            try:
                return json.loads(output_text[json_start:json_end])
            except json.JSONDecodeError:
                pass

        # If all parsing attempts fail, raise an error
        raise ValueError("Could not parse output as JSON")


def ensure_35_tags(tags, llm, title, platform, language):
    """Ensure we have exactly 35 tags using LangChain."""
    current_count = len(tags)

    if current_count == 35:
        return tags

    if current_count < 35:
        # Generate more tags
        more_tags_template = """
        Based on these existing tags for a {platform} video about "{title}":
        {tags}
        
        Generate {num_needed} additional relevant and trending tags in {language}.
        Return ONLY a JSON array with the new tags.
        """

        more_tags_prompt = PromptTemplate(
            input_variables=["platform", "title", "tags", "num_needed", "language"],
            template=more_tags_template,
        )

        more_tags_chain = LLMChain(llm=llm, prompt=more_tags_prompt)

        try:
            more_tags_result = more_tags_chain.run(
                platform=platform,
                title=title,
                tags=tags,
                num_needed=35 - current_count,
                language=language,
            )

            # Parse the additional tags
            try:
                additional_tags = parse_langchain_output(more_tags_result)
                if isinstance(additional_tags, list):
                    tags.extend(additional_tags[: 35 - current_count])
                else:
                    # Handle case where we get an object with a key instead of direct array
                    for key in additional_tags:
                        if isinstance(additional_tags[key], list):
                            tags.extend(additional_tags[key][: 35 - current_count])
                            break
            except:
                # Add generic tags if parsing fails
                for i in range(current_count, 35):
                    tags.append(f"related_tag_{i}")
        except:
            # Add generic tags if LangChain fails
            for i in range(current_count, 35):
                tags.append(f"related_tag_{i}")

    elif current_count > 35:
        # Truncate to exactly 35
        tags = tags[:35]

    return tags


def generate_fallback_seo(title, platform, language):
    """Generate fallback SEO content if parsing fails."""
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
    """Generate fallback thumbnail concepts if parsing fails."""
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
