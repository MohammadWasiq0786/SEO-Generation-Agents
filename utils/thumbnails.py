from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os
import colorsys
import math
from euriai import EuriaiClient

from dotenv import load_dotenv

load_dotenv()


def generate_thumbnail_with_dalle(client, concept, video_title, platform="YouTube"):
    """Generate a thumbnail image using DALL-E based on the concept and video title."""
    try:
        # Define aspect ratio based on platform
        if platform == "YouTube":
            aspect_ratio = "16:9"
            size = "1792x1024"  # DALL-E supports 1792x1024 which is close to 16:9
        elif platform == "Instagram":
            aspect_ratio = "1:1"
            size = "1024x1024"  # Square format for Instagram
        elif platform == "LinkedIn":
            aspect_ratio = "1.91:1"
            size = "1792x1024"  # Using same as YouTube for now
        else:
            aspect_ratio = "16:9"  # Default to YouTube ratio
            size = "1792x1024"

        # Extract key elements from the concept
        text_overlay = concept.get("text_overlay", "")
        focal_point = concept.get("focal_point", "")
        tone = concept.get("tone", "")
        concept_desc = concept.get("concept", "")

        # Get colors for text if available
        colors = concept.get("colors", ["#FFFFFF", "#000000"])
        main_color = colors[0] if len(colors) > 0 else "#FFFFFF"

        # Craft a detailed prompt for DALL-E that includes the text overlay
        prompt = f"""
        Create a professional {platform} thumbnail with these specifications:
        - Clear {aspect_ratio} format for {platform}
        - Main focus: {focal_point}
        - Emotional tone: {tone}
        - Bold, clear text overlay reading "{text_overlay}" prominently displayed
        - Text should be highly legible, possibly in color {main_color} with contrasting outline
        - Concept: {concept_desc}
        - Related to: {video_title}
        - Professional, eye-catching design with high contrast
        - Make sure the text stands out and is easily readable
        - Thumbnail should look professional and high-quality for {platform}
        - Text should be integrated with the visual elements in a visually appealing way
        """

        # Generate the image with DALL-E

        # client = EuriaiClient(
        #     api_key=os.getenv("EURIAI_API_KEY"),
        #     model="gemini-2.5-pro-exp-03-25",  # You can also try: "gemini-2.0-flash-001", "llama-4-maverick", etc.
        # )

        response = client.generate_completion(
            prompt=prompt, size=size, quality="standard"
        )

        # Get the image URL
        image_url = response.data[0].url
        return image_url

    except Exception as e:
        print(f"Error generating thumbnail with DALL-E: {e}")
        return None


def create_gradient_background(concept, width=1280, height=720):
    """Create a gradient background using the colors from the concept."""
    # Get colors from concept, or use defaults
    colors = concept.get("colors", ["#3366CC", "#FFFFFF", "#FF5555"])

    # Ensure we have at least two colors
    if len(colors) < 2:
        colors.append("#FFFFFF")

    # Parse hex colors to RGB
    try:
        color1 = hex_to_rgb(colors[0])
        color2 = hex_to_rgb(colors[1] if len(colors) > 1 else "#FFFFFF")
    except:
        # Fallback to default colors if parsing fails
        color1 = (51, 102, 204)  # #3366CC
        color2 = (255, 255, 255)  # #FFFFFF

    # Create a new image
    img = Image.new("RGB", (width, height), color=color1)
    draw = ImageDraw.Draw(img)

    # Create gradient
    for y in range(height):
        # Calculate ratio of current position
        ratio = y / height

        # Interpolate between the two colors
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)

        # Draw a line with the interpolated color
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Add a subtle pattern based on the tone
    tone = concept.get("tone", "").lower()
    if "professional" in tone or "educational" in tone:
        add_professional_pattern(img, draw)
    elif "energetic" in tone or "exciting" in tone:
        add_energetic_pattern(img, draw)
    elif "emotional" in tone or "dramatic" in tone:
        add_dramatic_pattern(img, draw)

    return img


def add_text_with_outline(img, draw, concept):
    """Add text overlay with outline for better visibility."""
    text = concept.get("text_overlay", "THUMBNAIL")
    colors = concept.get("colors", ["#FFFFFF", "#000000"])

    # Get text color and outline color
    text_color = colors[0] if len(colors) > 0 else "#FFFFFF"
    outline_color = colors[1] if len(colors) > 1 else "#000000"

    # Parse hex colors to RGB
    try:
        text_rgb = hex_to_rgb(text_color)
        outline_rgb = hex_to_rgb(outline_color)
    except:
        # Fallback colors
        text_rgb = (255, 255, 255)
        outline_rgb = (0, 0, 0)

    # Try to use a font if available
    try:
        # Try common system fonts
        system_fonts = [
            "arial.ttf",
            "Arial.ttf",
            "Verdana.ttf",
            "verdana.ttf",
            "impact.ttf",
            "Impact.ttf",
            "Tahoma.ttf",
            "tahoma.ttf",
        ]

        font = None
        for font_name in system_fonts:
            try:
                font = ImageFont.truetype(font_name, 80)
                break
            except IOError:
                continue

        # If no system font is found, use default
        if font is None:
            font = ImageFont.load_default().font_variant(size=80)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Get text size for centering
    try:
        _, _, text_width, text_height = draw.textbbox((0, 0), text, font=font)
    except:
        # Estimate size if method not available
        text_width = len(text) * 40
        text_height = 80

    # Calculate text position (centered by default)
    position = ((img.width - text_width) // 2, (img.height - text_height) // 2)

    # Check if composition indicates different text placement
    composition = concept.get("composition", "").lower()
    if "top" in composition:
        position = (position[0], img.height // 4)
    elif "bottom" in composition:
        position = (position[0], img.height * 3 // 4)
    elif "left" in composition:
        position = (img.width // 4, position[1])
    elif "right" in composition:
        position = (img.width * 3 // 4 - text_width, position[1])

    # Draw text outline
    outline_size = 3
    for x_offset in range(-outline_size, outline_size + 1, outline_size):
        for y_offset in range(-outline_size, outline_size + 1, outline_size):
            draw.text(
                (position[0] + x_offset, position[1] + y_offset),
                text,
                font=font,
                fill=outline_rgb,
            )

    # Draw main text
    draw.text(position, text, font=font, fill=text_rgb)


def add_watermark(img, draw):
    """Add a subtle watermark to the image."""
    watermark_text = "Video SEO Optimizer"
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    # Draw watermark in bottom right corner
    draw.text(
        (img.width - 220, img.height - 30),
        watermark_text,
        fill=(255, 255, 255, 128),
        font=font,
    )


def add_professional_pattern(img, draw):
    """Add a subtle professional pattern to the background."""
    width, height = img.size

    # Draw subtle lines
    for i in range(0, width, 40):
        draw.line([(i, 0), (i, height)], fill=(255, 255, 255, 10))

    for i in range(0, height, 40):
        draw.line([(0, i), (width, i)], fill=(255, 255, 255, 10))


def add_energetic_pattern(img, draw):
    """Add an energetic pattern to the background."""
    width, height = img.size

    # Draw diagonal lines
    for i in range(-height, width + height, 60):
        draw.line([(i, 0), (i + height, height)], fill=(255, 255, 255, 15))
        draw.line([(i, height), (i + height, 0)], fill=(255, 255, 255, 15))


def add_dramatic_pattern(img, draw):
    """Add a dramatic pattern to the background."""
    width, height = img.size
    center_x, center_y = width // 2, height // 2

    # Draw concentric circles
    for radius in range(50, max(width, height), 100):
        draw.arc(
            [
                (center_x - radius, center_y - radius),
                (center_x + radius, center_y + radius),
            ],
            0,
            360,
            fill=(255, 255, 255, 20),
        )


def hex_to_rgb(hex_color):
    """Convert hex color code to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def create_thumbnail_preview(concept, video_title, base_image_url=None):
    """
    Create a thumbnail preview based on concept description.
    This generates a basic visualization when DALL-E is not available.
    """
    # If we have a base image URL (like YouTube thumbnail), we can use it
    if base_image_url:
        try:
            response = requests.get(base_image_url)
            img = Image.open(BytesIO(response.content))
            # Resize to standard thumbnail size if needed
            img = img.resize((1280, 720))
        except Exception:
            # Fallback to creating a blank image
            img = create_gradient_background(concept)
    else:
        # Create a background with gradient using the concept colors
        img = create_gradient_background(concept)

    # Create a drawing context
    draw = ImageDraw.Draw(img)

    # Add text overlay if specified
    if concept.get("text_overlay"):
        add_text_with_outline(img, draw, concept)

    # Add a subtle watermark
    add_watermark(img, draw)

    return img
