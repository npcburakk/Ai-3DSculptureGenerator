"""
Prompt Enhancement Service — OpenAI ile 3D model prompt'larını optimize eder
"""

import logging
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

STYLE_DESCRIPTIONS = {
    # Sculpture / Classic
    "marble": "white marble material, classical sculpture, smooth polished surface, museum quality, renaissance style",
    "stone": "rough stone material, ancient carved, weathered texture, monolithic, chiseled details",
    "bronze": "bronze metal material, oxidized patina, classical sculpture, detailed casting, museum piece",
    "clay": "clay sculpture, handcrafted, matte earthy surface, artisan made, terracotta tones",
    # Modern / Sci-Fi
    "cyberpunk": "cyberpunk style, neon accents, mechanical parts, chrome and metal, sci-fi dystopian",
    "futuristic": "futuristic design, sleek surfaces, advanced technology aesthetic, clean lines, sci-fi",
    "robotic": "robotic mechanical structure, metal panels, gears and bolts, industrial, engineered",
    "neon_glow": "neon glowing material, vibrant emission, dark background contrast, luminescent edges",
    # Stylized / Game
    "cartoon": "cartoon style, exaggerated proportions, smooth rounded surfaces, playful, colorful",
    "stylized": "stylized game art, semi-realistic, detailed but artistic, cinematic game quality",
    "low_poly": "low poly art style, geometric facets, minimal polygons, clean sharp angles",
    "pixar": "Pixar animation style, soft rounded forms, expressive, high quality 3D animation",
    # Material Effects
    "glass": "transparent glass material, refractive, clear crystal, delicate thin walls, optical",
    "ice": "frozen ice material, crystalline structure, transparent blue tones, cold and reflective",
    "wood": "carved wood material, natural grain texture, artisan craftsmanship, warm organic tones",
    "gold": "solid gold material, ornate luxury finish, highly reflective, precious metal gleam",
    # Organic / Fantasy
    "alien": "alien organic structure, otherworldly biomechanical, strange proportions, extraterrestrial",
    "fantasy": "high fantasy style, magical aesthetic, ornate details, epic scale, mythological",
    "dragon": "dragon scale texture, reptilian detail, fantasy creature, fierce and ancient",
    "organic": "organic flowing forms, natural curves, biological structure, living tissue appearance",
    # Minimal / Abstract
    "abstract": "abstract art sculpture, non-representational, artistic interpretation, conceptual form",
    "geometric": "pure geometric shapes, mathematical precision, clean angles, modern minimalist",
    "minimal": "minimalist design, essential form only, negative space, refined simplicity",
    "parametric": "parametric design, algorithmic curves, computational geometry, architectural avant-garde",
    # Default
    "realistic": "photorealistic, highly detailed, accurate proportions, natural materials, 8k quality",
}

SYSTEM_PROMPT = """You are an expert at writing prompts for AI 3D model generation systems like Meshy AI and Shap-E.
Your task is to enhance user prompts to produce higher quality, more detailed 3D models.

Rules:
- Keep the core subject the same
- Add material, texture, lighting, and quality descriptors
- Add geometric/structural details that help 3D generation
- Keep it under 200 characters
- Output ONLY the enhanced prompt, nothing else
- Write in English"""


class PromptService:
    async def enhance(self, prompt: str, style: str = "realistic") -> dict:
        """
        Prompt'u OpenAI ile geliştirir.
        Returns: { original, enhanced, style }
        """
        if not settings.OPENAI_API_KEY:
            return {"original": prompt, "enhanced": prompt, "style": style}

        # Key'i her çağrıda taze okur (self.client'ta önbelleklemez) — aksi
        # halde Ayarlar ekranından key sonradan girildiğinde, uygulama
        # başında boş key ile oluşturulmuş bir client kalıcı olarak
        # kullanılmaya devam ederdi.
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        style_desc = STYLE_DESCRIPTIONS.get(style, "")

        user_message = f"""Enhance this 3D model prompt: "{prompt}"
Style: {style} - {style_desc}
Output only the enhanced prompt."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=200,
                temperature=0.7,
            )
            enhanced = response.choices[0].message.content.strip()
            logger.info(f"Prompt enhanced: '{prompt}' → '{enhanced}'")
            return {"original": prompt, "enhanced": enhanced, "style": style}
        except Exception as e:
            logger.error(f"Prompt enhancement failed: {e}")
            return {"original": prompt, "enhanced": prompt, "style": style}
