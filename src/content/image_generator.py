import httpx
import io
from typing import Optional
from config.settings import settings


class ImageGenerator:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate_image(self, prompt: str, size: str = "1024x1024") -> Optional[str]:
        providers = []
        if settings.hf_token:
            providers.append(("HuggingFace/FLUX", self._generate_with_hf))
        if settings.groq_api_key:
            providers.append(("Groq", self._generate_with_groq))
        if settings.openrouter_api_key:
            providers.append(("OpenRouter", self._generate_with_openrouter))
        if settings.cerebras_api_key:
            providers.append(("Cerebras", self._generate_with_cerebras))

        for provider_name, generate in providers:
            try:
                image = await generate(prompt, size)
                if image:
                    return image
            except Exception as exc:
                print(f"{provider_name} image generation error: {exc}")
        return None

    async def _generate_with_hf(self, prompt: str, size: str) -> Optional[str]:
        from huggingface_hub import InferenceClient
        
        client = InferenceClient(
            provider="fal-ai",
            api_key=settings.hf_token,
        )
        
        # FLUX.1-dev works best with 1024x1024
        image = client.text_to_image(
            prompt,
            model="black-forest-labs/FLUX.1-dev",
        )
        
        # Convert PIL Image to bytes
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="PNG")
        return img_bytes.getvalue()

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

    async def _generate_with_openrouter(self, prompt: str, size: str) -> Optional[str]:
        import openai
        client = openai.OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        response = client.images.generate(
            model="openai/dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )

        if response.data and response.data[0].url:
            img_response = await self.client.get(response.data[0].url)
            if img_response.status_code == 200:
                return img_response.content
        return None

    async def _generate_with_cerebras(self, prompt: str, size: str) -> Optional[str]:
        import openai
        client = openai.OpenAI(
            api_key=settings.cerebras_api_key,
            base_url="https://api.cerebras.ai/v1",
        )

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )

        if response.data and response.data[0].url:
            img_response = await self.client.get(response.data[0].url)
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