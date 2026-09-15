from pydantic.dataclasses import dataclass

from melon.core.base.parsers.components.settings import CustomSettingsTemplate

from .src.enums import ImagesServersTypes

@dataclass(frozen = True)
class CustomSettingsModel(CustomSettingsTemplate):
	"""Кастомные параметры парсера."""

	token: str | None
	images_server: ImagesServersTypes
	add_moderation_status: bool
	add_free_publication_date: bool
