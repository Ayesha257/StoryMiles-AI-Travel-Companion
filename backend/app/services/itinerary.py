from datetime import timedelta
from uuid import UUID

from app.models.enums import TripStatus
from app.repositories.itinerary import ItineraryRepository
from app.schemas.itinerary import ItineraryGenerateRequest, ItineraryResponse
from app.services.ai_client import AIClient


class ItineraryGenerator:
    def __init__(self, ai_client: AIClient, repository: ItineraryRepository) -> None:
        self.ai_client = ai_client
        self.repository = repository

    async def generate(self, user_id: UUID, request: ItineraryGenerateRequest) -> ItineraryResponse:
        itinerary_data = await self.ai_client.complete_json(
            "You are a practical, safety-conscious travel planner. Create a geographically sensible day-by-day itinerary.",
            f"Destination: {request.destination}, {request.country or ''}\nDays: {request.days}\nTravelers: {request.travelers_count}\nBudget: {request.budget_level}\nInterests: {request.interests}\nNotes: {request.additional_notes or ''}\nReturn {{'summary':'','days':[{{'day':1,'title':'','activities':[{{'time':'','activity':'','location':'','estimated_cost':'','tips':['']}}], 'meals':[''], 'transportation':'', 'daily_budget':''}}], 'total_estimated_budget':'', 'packing_tips':[''], 'travel_tips':['']}}.",
        )
        start_date = request.start_date
        end_date = request.end_date or (start_date + timedelta(days=request.days - 1) if start_date else None)
        itinerary = await self.repository.create(
            user_id=user_id,
            title=f"{request.days}-Day {request.destination} Itinerary",
            summary=str(itinerary_data.get("summary", "")) or None,
            start_date=start_date,
            end_date=end_date,
            travelers_count=request.travelers_count,
            status=TripStatus.DRAFT,
            generated_by_model=self.ai_client.model,
            itinerary_data=itinerary_data,
        )
        return ItineraryResponse.model_validate(itinerary)
