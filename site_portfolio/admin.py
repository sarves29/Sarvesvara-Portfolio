from django.contrib import admin, messages
from .models import Project, Resume
from PyPDF2 import PdfReader
from docx import Document
from google import genai
import os
import json
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

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            # 3️⃣ Debug

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
            messages.error(request, f"❌ Error processing resume: {type(e).__name__}")
