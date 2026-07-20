import asyncio
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.core.config import settings


class AlbumPDFService:
    async def generate(self, album: object) -> bytes:
        return await asyncio.to_thread(self._generate_sync, album)

    def _generate_sync(self, album: object) -> bytes:
        output = BytesIO()
        page_width, page_height = landscape(A4)
        document = canvas.Canvas(output, pagesize=(page_width, page_height))
        document.setTitle(getattr(album, "title"))

        self._draw_cover(document, album, page_width, page_height)
        for photo in getattr(album, "photos", []):
            self._draw_photo(document, album, photo, page_width, page_height)

        document.save()
        return output.getvalue()

    @staticmethod
    def _draw_cover(document: canvas.Canvas, album: object, width: float, height: float) -> None:
        document.setFillColor(colors.HexColor("#10263D"))
        document.rect(0, 0, width, height, fill=1, stroke=0)
        document.setFillColor(colors.HexColor("#E3A63C"))
        document.setFont("Helvetica-Bold", 12)
        document.drawString(54, height - 64, "STORYMILES · TRIP ALBUM")
        document.setFillColor(colors.white)
        document.setFont("Helvetica-Bold", 34)
        document.drawString(54, height - 130, getattr(album, "title"))

        destination = getattr(album, "destination", None)
        if destination:
            document.setFont("Helvetica", 18)
            document.setFillColor(colors.HexColor("#F2EDE2"))
            document.drawString(54, height - 168, destination)

        dates = [
            value.strftime("%B %d, %Y")
            for value in (getattr(album, "trip_start", None), getattr(album, "trip_end", None))
            if value
        ]
        if dates:
            document.setFont("Helvetica", 11)
            document.drawString(54, height - 198, " — ".join(dates))

        description = getattr(album, "description", None)
        if description:
            document.setFont("Helvetica", 11)
            document.setFillColor(colors.HexColor("#FAF9F6"))
            document.drawString(54, 64, description[:120])
        document.showPage()

    @staticmethod
    def _draw_photo(
        document: canvas.Canvas, album: object, photo: object, width: float, height: float
    ) -> None:
        document.setFillColor(colors.HexColor("#FAF9F6"))
        document.rect(0, 0, width, height, fill=1, stroke=0)

        image = getattr(photo, "image")
        image_path = Path(settings.upload_directory).resolve() / getattr(image, "storage_key")
        if image_path.exists():
            reader = ImageReader(str(image_path))
            image_width, image_height = reader.getSize()
            available_width = width - 96
            available_height = height - 120
            scale = min(available_width / image_width, available_height / image_height)
            draw_width = image_width * scale
            draw_height = image_height * scale
            document.drawImage(
                reader,
                (width - draw_width) / 2,
                58 + (available_height - draw_height) / 2,
                draw_width,
                draw_height,
                preserveAspectRatio=True,
                mask="auto",
            )

        caption = getattr(photo, "caption", None) or getattr(image, "filename")
        document.setFillColor(colors.HexColor("#10263D"))
        document.setFont("Helvetica-Bold", 11)
        document.drawString(48, 30, caption[:100])
        document.setFont("Helvetica", 9)
        document.drawRightString(width - 48, 30, getattr(album, "title"))
        document.showPage()
