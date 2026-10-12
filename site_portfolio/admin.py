from django.contrib import admin, messages
from .models import Project, Resume
from PyPDF2 import PdfReader
from docx import Document
from google import genai
import os
import json
import time
from dotenv import load_dotenv
from django.utils.text import slugify
# ✅ Load environment variables early
load_dotenv()

try:
    from google import genai
except ImportError:
    genai = None
    print("⚠️ google-genai not installed. Run: pip install google-genai")

# ✅ Only initialize the Gemini client if key exists
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = None

if GOOGLE_API_KEY and genai:
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        print("✅ Gemini client initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini client: {e}")
else:
    print("⚠️ GOOGLE_API_KEY not found or genai missing — skipping Gemini setup.")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "featured", "order", "created_at")
    list_editable = ("featured", "order")
    prepopulated_fields = {"slug": ("title",)}


def extract_text_from_file(file_path):
    """Extract text from PDF or DOCX resumes."""
    if file_path.endswith(".pdf"):
        text = ""
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text

    elif file_path.endswith(".docx"):
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

    else:
        raise ValueError("Unsupported file format")


GEMINI_MODELS = ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro")


def _generate_with_retry(prompt, max_attempts=4):
    """Call Gemini with exponential backoff; rotate through fallback models on 503."""
    last_err = None
    for model in GEMINI_MODELS:
        for attempt in range(max_attempts):
            try:
                return client.models.generate_content(model=model, contents=prompt)
            except Exception as e:
                msg = str(e)
                last_err = e
                transient = "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg.lower()
                if not transient:
                    raise
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                break
    raise last_err

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("title", "processed", "uploaded_at")
    readonly_fields = ("processed",)

    def save_model(self, request, obj, form, change):
        """Automatically process the resume with Gemini when uploaded."""
        super().save_model(request, obj, form, change)

        if obj.processed:
            messages.info(request, f"ℹ️ Resume '{obj.title}' already processed.")
            return

        if not client:
            messages.error(request, "⚠️ Gemini client not available.")
            return

        try:
            # 1️⃣ Extract text
            file_path = obj.file.path
            resume_text = extract_text_from_file(file_path)

            # 2️⃣ Send prompt to Gemini
            prompt = f"""
            You are an expert resume analyzer.
            Extract only *technical projects or practical works* from the resume.
            Include:
            - college projects
            - internships
            - freelance or professional work
            - research projects

            Return JSON only, with structure:
            [
              {{
                "title": "Project Name",
                "description": "Brief summary of the project.",
                "technologies": ["Python", "Django", "React"]
              }}
            ]

            Resume text:
            {resume_text}
            """

            response = _generate_with_retry(prompt)

            # 3️⃣ Debug
            print("🧠 Gemini raw output:\n", response.text)

            raw_output = response.text.strip().replace("```json", "").replace("```", "")
            try:
                projects = json.loads(raw_output)
            except json.JSONDecodeError:
                messages.error(request, "⚠️ Gemini returned invalid JSON.")
                return

            added, updated = 0, 0

            # 4️⃣ Create or update projects
            for data in projects:
                title = data.get("title", "").strip()
                if not title:
                    continue

                defaults = {
                    "short_summary": data.get("description", "")[:300],
                    "long_description": data.get("description", ""),
                    "tech_list": ", ".join(data.get("technologies", [])),
                }

                existing = Project.objects.filter(title__iexact=title).first()
                if existing:
                    for k, v in defaults.items():
                        setattr(existing, k, v)
                    existing.save()
                    updated += 1
                else:
                    Project.objects.create(title=title, slug=slugify(title), **defaults)
                    added += 1

            # 5️⃣ Mark as processed
            obj.processed = True
            obj.save(update_fields=["processed"])

            messages.success(
                request,
                f"✅ Resume '{obj.title}' processed — {added} added, {updated} updated."
            )

        except Exception as e:
            msg = str(e)
            if "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg.lower():
                messages.error(
                    request,
                    "❌ Gemini is temporarily overloaded (503). Resume saved — click Save again in a minute to retry processing.",
                )
            else:
                messages.error(request, f"❌ Error processing resume: {e}")
