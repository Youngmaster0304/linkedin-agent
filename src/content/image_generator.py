import base64
import httpx
from typing import Optional
from config.settings import settings


class ImageGenerator:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate_image(self, prompt: str, size: str = "1024x1024") -> Optional[str]:
        try:
            if settings.openai_api_key:
                return await self._generate_with_openai(prompt, size)
            elif settings.gemini_api_key:
                return await self._generate_with_gemini(prompt, size)
            elif settings.groq_api_key:
                return await self._generate_with_groq(prompt, size)
            else:
                return None
        except Exception as e:
            print(f"Image generation error: {e}")
            return None

    async def _generate_with_openai(self, prompt: str, size: str) -> Optional[str]:
        import openai
        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )
        
        if response.data and response.data[0].url:
            async with httpx.AsyncClient() as client:
                img_response = await client.get(response.data[0].url)
                if img_response.status_code == 200:
                    return img_response.content
        return None

    async def _generate_with_gemini(self, prompt: str, size: str) -> Optional[str]:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        
        model = genai.GenerativeModel('gemini-pro-vision')
        
        response = model.generate_content([
            "Generate an image for this LinkedIn post:",
            prompt,
            "Make it professional, clean, and suitable for LinkedIn."
        ])
        
        if response.candidates and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            if hasattr(part, 'inline_data') and part.inline_data:
                return part.inline_data.data
        return None

    async def _generate_with_groq(self, prompt: str, size: str) -> Optional[str]:
        import groq
        client = groq.Groq(api_key=settings.groq_api_key)
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )
        
        if response.data and response.data[0].url:
            async with httpx.AsyncClient() as client:
                img_response = await client.get(response.data[0].url)
                if img_response.status_code == 200:
                    return img_response.content
        return None

    async def generate_placeholder_image(self, topic: str, style: str = "professional") -> str:
        prompts = {
            "AI coding agents pricing 2026": "Professional comparison chart showing AI coding tool pricing in 2026, with bars for different tools",
            "agentic AI frameworks 2026": "Modern agentic AI architecture diagram with microservices and orchestration",
            "LLM inference optimization 2026": "Performance benchmark graph showing LLM inference optimization techniques",
            "Kubernetes AI workloads 2026": "Kubernetes cluster with GPU workloads and AI orchestration",
            "MLOps platforms 2026": "MLOps platform architecture with CI/CD pipeline",
            "vector databases comparison 2026": "Comparison of vector database architectures and indexing",
            "RAG evaluation frameworks 2026": "RAG evaluation metrics and assessment framework",
            "open source LLM fine-tuning 2026": "Open source LLM fine-tuning pipeline with training metrics",
            "AI safety alignment 2026": "AI safety alignment diagram showing alignment techniques",
            "quant finance AI applications 2026": "Financial charts and AI models for quantitative analysis",
        }
        
        base_prompt = prompts.get(topic, f"Professional infographic about {topic}")
        
        if style == "minimal":
            base_prompt += ", clean minimal design, blue and white color scheme"
        elif style == "tech":
            base_prompt += ", tech diagram, circuit patterns, blue gradients"
        
        return await self.generate_image(base_prompt, "1024x1024")

    async def close(self):
        await self.client.aclose()